import click
from click_option_group import optgroup

import typing

import multiprocessing
import pandas as pd
import tqdm

def filter_smiles(smiles: str, neutral_only: bool = True) -> bool:
    """Returns True if the pattern can be parameterized"""
    from openff.toolkit.topology.molecule import Molecule, unit
    from openff.toolkit.typing.engines.smirnoff import ForceField

    offmol = Molecule.from_smiles(smiles, allow_undefined_stereo=True)

    total_charge = int(
        sum(int(atom.formal_charge / unit.elementary_charge) for atom in offmol.atoms)
    )
    if total_charge and neutral_only:
        return False

    ff = ForceField("openff-2.1.0.offxml")
    try:
        ff.create_openmm_system(offmol.to_topology())
    except BaseException:
        return False
    return True


def filter_row(index_and_row, neutral_only: bool = True) -> bool:
    index, row = index_and_row
    smi1, smi2 = row["smiles0"], row["smiles1"]
    condition = (
        filter_smiles(smi1, neutral_only)
        and filter_smiles(smi2, neutral_only)
    )
    return index, condition

def batch_filter_row(
    indices_and_rows,
    neutral_only: bool = True,
) -> list[tuple[int, bool]]:

    indices_and_conditions = []
    for index_and_row in tqdm.tqdm(indices_and_rows, desc="Filtering rows"):
        indices_and_conditions.append(filter_row(index_and_row, neutral_only))

    return indices_and_conditions

@click.command()
@click.option(
    "--input",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.option(
    "--neutral-only/--no-neutral-only",
    "neutral_only",
    default=True,
    is_flag=True,
)
@optgroup.group("Parallelization configuration")
@optgroup.option(
    "--n-workers",
    help="The number of workers to distribute the labelling across. Use -1 to request "
    "one worker per batch.",
    type=int,
    default=1,
    show_default=True,
)
@optgroup.option(
    "--worker-type",
    help="The type of worker to distribute the labelling across.",
    type=click.Choice(["lsf", "local", "slurm"]),
    default="local",
    show_default=True,
)
@optgroup.option(
    "--batch-size",
    help="The number of molecules to processes at once on a particular worker.",
    type=int,
    default=500,
    show_default=True,
)
@optgroup.group("LSF configuration", help="Options to configure LSF workers.")
@optgroup.option(
    "--memory",
    help="The amount of memory (GB) to request per LSF queue worker.",
    type=int,
    default=3,
    show_default=True,
)
@optgroup.option(
    "--walltime",
    help="The maximum wall-clock hours to request per LSF queue worker.",
    type=int,
    default=2,
    show_default=True,
)
@optgroup.option(
    "--queue",
    help="The LSF queue to submit workers to.",
    type=str,
    default="cpuqueue",
    show_default=True,
)
@optgroup.option(
    "--conda-environment",
    help="The conda environment that LSF workers should run using.",
    type=str,
)
def filter(
    output_file: str = "des15k-filtered.csv",
    input_file: str = "Donchev et al DES15K.csv",
    neutral_only: bool = True,
    worker_type: typing.Literal["lsf", "local"] = "local",
    queue: str = "cpuqueue",
    conda_environment: str = "openff-nagl",
    memory: int = 4,  # GB
    walltime: int = 32,  # hours
    batch_size: int = 300,
    n_workers: int = -1,
):

    from openff.nagl.utils._parallelization import batch_distributed
    from dask import distributed

    df = pd.read_csv(input_file)
    all_rows = list(df.iterrows())
    indices_and_conditions = []

    with batch_distributed(
        all_rows,
        batch_size=batch_size,
        worker_type=worker_type,
        queue=queue,
        conda_environment=conda_environment,
        memory=memory,
        walltime=walltime,
        n_workers=n_workers,
    ) as batcher:
        futures = list(
            batcher(
                batch_filter_row,
                neutral_only=neutral_only,
            )
        )
        for i, future in tqdm.tqdm(
            enumerate(distributed.as_completed(futures, raise_errors=False)),
            total=len(futures),
            desc="Saving rows",
        ):
            indices_and_conditions.extend(future.result())

    mask = [condition for index, condition in sorted(indices_and_conditions)]
    filtered = df[mask]

    print(f"Filtered {len(df) - len(filtered)} rows")
    print(f"Original length: {len(df)}")
    print(f"Filtered length: {len(filtered)}")

    filtered.to_csv(output_file)


if __name__ == "__main__":
    filter()