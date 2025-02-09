"""Train the force field."""
import contextlib
import datetime
import functools
import os
import pathlib
import click
import tqdm

import datasets
import datasets.distributed
import datasets.table
import pydantic
import smee
import tensorboardX
import torch
import torch.distributed

import descent.optim
import descent.targets.dimers
import descent.utils.loss
import descent.utils.reporting

import numpy as np

MISSING_SMILES = set()

WORLD_SIZE = torch.multiprocessing.cpu_count() - 2


@contextlib.contextmanager
def open_writer(path: pathlib.Path, rank: int) -> tensorboardX.SummaryWriter:
    if rank != 0:
        yield None
    else:
        path.mkdir(parents=True, exist_ok=True)

        with tensorboardX.SummaryWriter(str(path)) as writer:
            yield writer


class ParameterConfig(pydantic.BaseModel):
    """Configuration for how a potential's parameters should be trained."""

    cols: list[str] = pydantic.Field(
        description="The parameters to train, e.g. 'k', 'length', 'epsilon'."
    )

    exclude: list[str] = pydantic.Field(
        [],
        description="The parameters to exclude from training by SMIRKS.",
    )

    scales: dict[str, float] = pydantic.Field(
        {},
        description="The scales to apply to each parameter, e.g. 'k': 1.0, "
        "'length': 1.0, 'epsilon': 1.0.",
    )
    constraints: dict[str, tuple[float | None, float | None]] = pydantic.Field(
        {},
        description="The min and max values to clamp each parameter within, e.g. "
        "'k': (0.0, None), 'angle': (0.0, pi), 'epsilon': (0.0, None), where "
        "none indicates no constraint.",
    )


class TrainableParameters:
    """A wrapper around a SMEE force field that handles zeroing out gradients of
    fixed parameters and applying parameter constraints."""

    def __init__(
        self,
        force_field: smee.TensorForceField,
        parameters: dict[str, ParameterConfig],
    ):
        self.potential_types = [*parameters]
        self._force_field = force_field

        potentials = [
            force_field.potentials_by_type[potential_type]
            for potential_type in self.potential_types
        ]

        self._frozen_cols = [
            [
                i
                for i, col in enumerate(potential.parameter_cols)
                if col not in parameters[potential_type].cols
            ]
            for potential_type, potential in zip(self.potential_types, potentials)
        ]

        self._scales = [
            torch.tensor(
                [
                    parameters[potential_type].scales.get(col, 1.0)
                    for col in potential.parameter_cols
                ]
            ).reshape(1, -1)
            for potential_type, potential in zip(self.potential_types, potentials)
        ]
        self._constraints = [
            {
                i: parameters[potential_type].constraints[col]
                for i, col in enumerate(potential.parameter_cols)
                if col in parameters[potential_type].constraints
            }
            for potential_type, potential in zip(self.potential_types, potentials)
        ]

        self.parameters = [
            (potential.parameters.detach().clone() * scale).requires_grad_()
            for potential, scale in zip(potentials, self._scales)
        ]
        self._exclude = []
        for i, (potential_type, parameter_config) in enumerate(parameters.items()):
            potential = potentials[i]
            potential_parameters = self.parameters[i]
            for j, key in enumerate(potential.parameter_keys):
                if key.id in parameter_config.exclude or "EP" in key.id:
                    self._exclude.append((i, j, potential_parameters[j].clone().detach()))
        
        self.potentials = potentials

    @property
    def force_field(self) -> smee.TensorForceField:
        for potential_type, parameter, scale in zip(
            self.potential_types, self.parameters, self._scales
        ):
            potential = self._force_field.potentials_by_type[potential_type]
            potential.parameters = parameter / scale

        return self._force_field

    @torch.no_grad()
    def clamp(self):
        for parameter, constraints in zip(self.parameters, self._constraints):
            for i, (min_value, max_value) in constraints.items():
                if min_value is not None:
                    parameter[:, i].clamp_(min=min_value)
                if max_value is not None:
                    parameter[:, i].clamp_(max=max_value)
        for i, j, values in self._exclude:
            row = self.parameters[i][j]
            for x, val in enumerate(values):
                row[x].clamp_(min=val, max=val)

    @torch.no_grad()
    def freeze_grad(self):
        for parameter, col_idxs in zip(self.parameters, self._frozen_cols):
            parameter.grad[:, col_idxs] = 0.0


def write_metrics(
    i: int,
    loss: torch.Tensor,
    writer: tensorboardX.SummaryWriter,
):
    print(f"epoch={i} loss={loss:.6f}", flush=True)

    writer.add_scalar("loss", loss.detach().item(), i)
    writer.flush()



def fit(
    rank: int,
    input_dataset: str,
    input_force_field: str,
    parameterized_force_field: str,
    output_directory: str = None,
    n_epochs: int = 1000,
    lr: float = 0.01,
):
    
    from openff.toolkit import ForceField


    torch.set_num_threads(1)
    torch.distributed.init_process_group("gloo", rank=rank, world_size=WORLD_SIZE)

    force_field, topologies = torch.load(parameterized_force_field)

    trainable = TrainableParameters(
        force_field,
        {
            "vdW": ParameterConfig(
                cols=["epsilon", "sigma"],
                scales={"epsilon": 1.0, "sigma": 1.0},
                constraints={"epsilon": (0.01, None), "sigma": (0.0, None)},
                exclude=["[#1]-[#8X2H2+0:1]-[#1]", "[#1:1]-[#8X2H2+0]-[#1]", "[#6A:2]-[#17:1] EP", "[#6a:2]-[#17:1] EP", "[#6A:2]-[#35:1] EP", "[#6a:2]-[#35:1] EP", "[#6X3H1a:2]1:[#7X2a:1]:[#6X3H1a:3]:[#6X3a]:[#6X3a]:[#6X3a]1 EP"]
            ),
        },
    )

    dataset = datasets.Dataset.load_from_disk(input_dataset)
    dataset = dataset.filter(lambda x: not torch.any(torch.isnan(x["energy"])))
    n_entries = len(dataset)

    unique_smiles = descent.targets.dimers.extract_smiles(dataset)
    topologies = {k: v for k, v in topologies.items() if k in unique_smiles}

    dataset = datasets.distributed.split_dataset_by_node(
        dataset, rank=rank, world_size=WORLD_SIZE
    )

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # experiment_dir = pathlib.Path(f"outputs/runs/{timestamp}")
    experiment_dir = pathlib.Path(output_directory) # / f"run-{timestamp}"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    losses = []
    with open_writer(experiment_dir, rank) as writer:
        optimizer = torch.optim.Adam(trainable.parameters, lr=lr, amsgrad=True)

        if rank == 0:
            for v in tensorboardX.writer.hparams({"optimizer": "Adam", "lr": lr}, {}):
                writer.file_writer.add_summary(v)

        for i in range(n_epochs):

            e_ref, e_pred = descent.targets.dimers.predict(
                dataset, trainable.force_field, topologies
            )
            loss = ((e_pred - e_ref) ** 2).sum() / n_entries
            loss.backward()

            torch.distributed.all_reduce(loss)

            for parameter in trainable.parameters:
                torch.distributed.all_reduce(parameter.grad)

            trainable.freeze_grad()

            if rank == 0:
                write_metrics(i, loss, writer)

            optimizer.step()
            optimizer.zero_grad()

            trainable.clamp()
            losses.append(loss.item())

            if rank == 0 and i % 100 == 0:
                torch.save(
                    trainable.force_field, experiment_dir / f"force-field-epoch-{i}.pt"
                )

    if rank != 0:
        exit(0)

    for potential_type in trainable.potential_types:
        descent.utils.reporting.print_potential_summary(
            force_field.potentials_by_type[potential_type]
        )
        print("")

    np.savetxt(experiment_dir / "losses.dat", losses)
    torch.save(force_field, experiment_dir / "force-field.pt")

    output_forcefield = experiment_dir / "output.offxml"
    ff = ForceField(input_force_field)
    
    for potential_type in trainable.potential_types:
        potential = force_field.potentials_by_type[potential_type]
        handler = ff.get_parameter_handler(potential.type)

        for key, value in zip(potential.parameter_keys, potential.parameters.detach()):
            smirks = key.id
            # skip virtual particles
            if "EP" in smirks:
                continue

            parameter = handler[smirks]
            for index, col in enumerate(potential.parameter_cols):
                val = value[index].item() * potential.attribute_units[index]
                setattr(parameter, col, val)

    ff.to_file(str(output_forcefield))
    print(f"Force field written to {output_forcefield}")





@click.command()
@click.option(
    "--dataset",
    "input_dataset",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to the input dataset.",
)
@click.option(
    "--port",
    type=int,
    help="Port to use for distributed training.",
    default=57123,
)
@click.option(
    "--input-force-field",
    type=str,
    help="Path to the input force field.",
)
@click.option(
    "--output",
    "output_directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help="Path to the output directory.",
)
@click.option(
    "--parameterized-ff",
    "parameterized_force_field",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to the parameterized force field.",
)
@click.option(
    "--n-epochs",
    type=int,
    help="Number of epochs to train for.",
    default=1000,
)
@click.option(
    "--lr",
    type=float,
    help="Learning rate.",
    default=0.01,
)
def main(
    input_dataset: str,
    input_force_field: str,
    port: int,
    output_directory: str,
    parameterized_force_field: str,
    n_epochs: int = 1000,
    lr: float = 0.01,
):
    partial = functools.partial(
        fit,
        input_dataset=input_dataset,
        output_directory=output_directory,
        input_force_field=input_force_field,
        parameterized_force_field=parameterized_force_field,
        n_epochs=n_epochs,
        lr=lr,
    )
    os.environ["MASTER_ADDR"] = "localhost"
    os.environ["MASTER_PORT"] = str(port)

    torch.multiprocessing.spawn(partial, nprocs=WORLD_SIZE, join=True)

if __name__ == "__main__":
    main()
