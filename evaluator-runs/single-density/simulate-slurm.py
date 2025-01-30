import pickle
import click

from openff.units import unit
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.properties import Density, EnthalpyOfMixing
from openff.evaluator.client import RequestOptions

from openff.evaluator.backends import ComputeResources, QueueWorkerResources
from openff.evaluator.backends.dask import DaskLocalCluster
from openff.evaluator.backends.dask import DaskSLURMBackend

from openff.evaluator.client import EvaluatorClient, RequestOptions, ConnectionOptions
from openff.evaluator.server.server import EvaluatorServer
from openff.evaluator.utils.observables import ObservableType

from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.toolkit import ForceField



@click.command()
@click.option(
    "--dataset",
    "-d",
    "dataset_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default="dataset.json",
)
@click.option(
    "--n-molecules",
    "-n",
    type=int,
    default=2000,
)
@click.option(
    "--force-field",
    "-f",
    default="openff-2.2.1.offxml",
)
@click.option(
    "--port",
    "-p",
    default=8000,
)
@click.option(
    "--water-model",
    "-w",
    default="tip3p",
)
def main(
    dataset_path: str,
    n_molecules: int = 2000,
    force_field: str = "openff-2.2.1.offxml",
    water_model: str = "tip3p",
    port: int = 8000
):
    # load dataset
    dataset = PhysicalPropertyDataSet.from_json(dataset_path)
    print(f"Loaded {len(dataset.properties)} properties from {dataset_path}")

    options = RequestOptions()
    options.calculation_layers = ["SimulationLayer"]
    density_schema = Density.default_simulation_schema(
        n_molecules=n_molecules,
    )

    dhmix_schema = EnthalpyOfMixing.default_simulation_schema(
        n_molecules=n_molecules,
    )

    options.add_schema("SimulationLayer", "Density", density_schema)
    options.add_schema("SimulationLayer", "EnthalpyOfMixing", dhmix_schema)
    
    ff = ForceField(force_field, f"{water_model}.offxml")
    force_field_source = SmirnoffForceFieldSource.from_object(ff)

    worker_resources = QueueWorkerResources(
        number_of_threads=1,
        number_of_gpus=1,
        preferred_gpu_toolkit=ComputeResources.GPUToolkit.CUDA,
        per_thread_memory_limit=4 * unit.gigabyte,
        wallclock_time_limit="48:00:00",
    )

    backend = DaskSLURMBackend(
        minimum_number_of_workers=1,
        maximum_number_of_workers=23,  # 24 max on free queue -- keep 1 free.
        resources_per_worker=worker_resources,
        queue_name="free-gpu",
        setup_script_commands=[
            "source ~/.bashrc",
            "conda activate evaluator-test-env",
            "conda env export > conda-env.yaml",
        ],
        extra_script_options=["--gres=gpu:1"],
        adaptive_interval="1000ms",
    )
    backend.start()
    print("backend", backend)

    server = EvaluatorServer(
        calculation_backend=backend,
        working_directory="working-directory",
        delete_working_files=False,
        port=port,
    )
    server.start(asynchronous=True)
    client = EvaluatorClient(
        connection_options=ConnectionOptions(server_port=port)
    )

    request, error = client.request_estimate(
        dataset,
        force_field_source,
        options,
    )

    # block until computation finished
    results, exception = request.results(synchronous=True, polling_interval=30)
    assert exception is None

    print(f"Simulation complete")
    print(f"# estimated: {len(results.estimated_properties)}")
    print(f"# unsuccessful: {len(results.unsuccessful_properties)}")
    print(f"# exceptions: {len(results.exceptions)}")

    with open(f"{water_model}_results.pkl", "wb") as f:
        pickle.dump(results, f)

    output_path = f"{water_model}.json"
    results.estimated_properties.json(output_path, format=True)

if __name__ == "__main__":
    main()


