import click

import pickle

import absolv.config
import absolv.runner
import openmm.unit
import openff.toolkit

@click.command()
@click.option(
    "--forcefield",
    "forcefield_files",
    multiple=True,
    type=str,
    required=True,
    help="The force field files to use.",
)
def main(
    forcefield_files: list[str],
):
    
    system = absolv.config.System(
        solutes={"CCl": 1}, solvent_a=None, solvent_b={"O": 500},
    )

    temperature=298.15 * openmm.unit.kelvin
    pressure=1.0 * openmm.unit.atmosphere

    alchemical_protocol_a=absolv.config.EquilibriumProtocol(
        lambda_sterics=[1.0, 1.0, 1.0, 1.0, 1.0],
        lambda_electrostatics=[1.0, 0.75, 0.5, 0.25, 0.0]
    )
    alchemical_protocol_b=absolv.config.EquilibriumProtocol(
        lambda_sterics=[
            1.00, 1.00, 1.00, 1.00, 1.00, 0.95, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40,
            0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.00,
        ],
        lambda_electrostatics=[
            1.00, 0.75, 0.50, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
            0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
        ]
    )

    config = absolv.config.Config(
        temperature=temperature,
        pressure=pressure,
        alchemical_protocol_a=alchemical_protocol_a,
        alchemical_protocol_b=alchemical_protocol_b,
    )

    force_field = openff.toolkit.ForceField(*forcefield_files)
    prepared_system_a, prepared_system_b = absolv.runner.setup(system, config, force_field)

    result = absolv.runner.run_eq(
        config, prepared_system_a, prepared_system_b, "CUDA", output_dir="."
    )

    with open("result.pkl", "wb") as file:
        pickle.dump(result, file)


if __name__ == "__main__":
    main()
