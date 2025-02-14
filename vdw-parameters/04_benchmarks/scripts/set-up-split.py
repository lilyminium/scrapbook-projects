import copy
import json
import pathlib
import shutil
import tqdm
import click
import re



COMPUTERS = {
    "hpc3": {
        "backend_config": {
            "type": "dask-hpc",
            "cluster_type": "slurm",
            "minimum_workers": 1,
            "maximum_workers": 1,
            "resources_per_worker": {
                "n_processes": 1,
                "n_gpus": 1,
                "memory_limit": 16,
                "wallclock_time_limit": "23:59:00",
            },
            "queue_name": "free-gpu",
            "setup_script_commands": ["source ~/.bashrc", "conda activate ENVIRONMENT", "echo ENVIRONMENT"],
            "extra_script_options": [],
        },
        "working_directory": "working-directory",
        "enable_data_caching": None,
    },
    "lilac": {
        "backend_config": {
            "type": "dask-hpc",
            "cluster_type": "lsf",
            "minimum_workers": 1,
            "maximum_workers": 1,
            "resources_per_worker": {
                "n_processes": 1,
                "n_gpus": 1,
                "memory_limit": 16,
                "wallclock_time_limit": "23:59",
            },
            "queue_name": "gpuqueue",
            "setup_script_commands": ["source ~/.bashrc", "micromamba activate ENVIRONMENT", "echo ENVIRONMENT"],
            "extra_script_options": [],
        },
        "working_directory": "working-directory",
        "enable_data_caching": None,
    },
}


@click.command()
@click.option(
    "--forcefield",
    type=str,
    default="openff-2.1.0.offxml",
)
@click.option(
    "--dataset",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default="test-set-collection.json",
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
)
@click.option(
    "--computer",
    type=click.Choice(COMPUTERS.keys()),
)
@click.option(
    "--port",
    type=int,
)
@click.option(
    "--environment",
    type=str,
)
def main(
    output_directory: str,
    computer: str,
    port: int,
    forcefield: str = "openff-2.1.0.offxml",
    dataset: str = "test-set-collection.json",
    environment: str = "openff-sage"
):
    from openff.toolkit.typing.engines.smirnoff import ForceField
    from openff.evaluator.client import RequestOptions

    options = RequestOptions()
    options.calculation_layers = ["SimulationLayer"]


    with open(dataset, "r") as f:
        contents = json.load(f)

    all_entries = contents.pop("entries")

    for i, entry in enumerate(tqdm.tqdm(all_entries), 1):

        directory = pathlib.Path(output_directory) / f"entry-{i:05d}"
        directory.mkdir(exist_ok=True, parents=True)

        server_config = copy.deepcopy(COMPUTERS[computer])
        server_config["port"] = port + i
        commands = []
        for command in server_config["backend_config"]["setup_script_commands"]:
            commands.append(re.sub("ENVIRONMENT", environment, command))
        server_config["backend_config"]["setup_script_commands"] = commands

        server_config_file = directory / "server-config.json"
        with server_config_file.open("w") as f:
            json.dump(server_config, f)

        estimation_options_file = directory / "estimation-options.json"
        options.json(str(estimation_options_file), format=True)

        ff = ForceField(forcefield, allow_cosmetic_attributes=True)
        output_ff = directory / "force-field.offxml"
        ff.to_file(output_ff, discard_cosmetic_attributes=True)

        dataset = {
            "data_sets": [copy.deepcopy(contents)]
        }
        dataset["data_sets"][0]["entries"] = [entry]
        dataset_file = directory / "test-set-collection.json"
        with dataset_file.open("w") as f:
            json.dump(dataset, f)



if __name__ == "__main__":
    main()
