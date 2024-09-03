import click

from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.evaluator.backends import ComputeResources
from openff.evaluator.backends.dask import DaskLocalCluster
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.server import EvaluatorServer
from openff.evaluator.client import EvaluatorClient, ConnectionOptions
from openff.evaluator.client import RequestOptions
from openff.evaluator.properties import Density, EnthalpyOfMixing, SolvationFreeEnergy

@click.command()
@click.option(
    "--input",
    "input_dataset",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="The path to the JSON file containing the PhysicalPropertyDataSet to evaluate.",
)
@click.option(
    "--forcefield",
    "forcefield_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="The path to the SMIRNOFF force field to evaluate the properties with. JSON or OFFXML",
)
@click.option(
    "--output",
    "output_path",
    default="results.json",
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    help="The path to write the evaluated results to.",
)
@click.option(
    "--options",
    "options_path",
    default=None,
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    help="The path to the JSON file containing the RequestOptions to use.",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="The port to start the evaluator server on.",
)
def main(
    input_dataset: str,
    forcefield_path: str,
    port: int,
    options_path: str = None,
    output_path: str = "results.json",
):
    # load force field and data
    if forcefield_path.endswith("offxml"):
        force_field_source = SmirnoffForceFieldSource.from_path(forcefield_path)
    else:
        force_field_source = SmirnoffForceFieldSource.from_json(forcefield_path)
    dataset = PhysicalPropertyDataSet.from_json(input_dataset)

    calculation_backend = DaskLocalCluster(
        number_of_workers=1,
        resources_per_worker=ComputeResources(
            number_of_threads=1,
            number_of_gpus=1,
            preferred_gpu_toolkit=ComputeResources.GPUToolkit.CUDA,
        ),
    )
    calculation_backend.start()

    evaluator_server = EvaluatorServer(
        calculation_backend=calculation_backend,
        port=port,
        delete_working_files=False
    )
    evaluator_server.start(asynchronous=True)

    connection_options = ConnectionOptions(server_port=port)
    evaluator_client = EvaluatorClient(connection_options=connection_options)

    if options_path:
        options = RequestOptions.from_json(options_path)
    else:
        options = RequestOptions()
        options.calculation_layers = ["SimulationLayer"]
        options.add_schema(
            "SimulationLayer",
            "SolvationFreeEnergy",
            SolvationFreeEnergy.default_simulation_schema(),
        )
        

    request, exception = evaluator_client.request_estimate(
        property_set=dataset,
        force_field_source=force_field_source,
        options=options
    )

    results, exception = request.results(synchronous=True, polling_interval=30)
    assert exception is None, exception

    if results.estimated_properties:
        results.estimated_properties.json(output_path, format=True)
    else:
        print(f"No properties were estimated.")
        print(results.unsuccessful_properties)
        print(results.queued_properties)
        print("exceptions")
        print(results.exceptions)



if __name__ == "__main__":
    main()
