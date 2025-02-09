import click
import pathlib
import torch


@click.command()
@click.option(
    "--input",
    "input_directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to the input directory.",
)
@click.option(
    "--force-field",
    "input_force_field",
    type=str,
    help="Path to the input force field.",
)
def main(
    input_directory: str,
    input_force_field: str,
):
    from openff.toolkit import ForceField
    from openff.units import unit

    input_directory = pathlib.Path(input_directory)
    force_field = torch.load(input_directory / "force-field.pt")

    ff = ForceField(input_force_field)
    
    for potential_type in ["vdW"]:
        potential = force_field.potentials_by_type[potential_type]
        print(potential.parameter_cols)
        print(potential.attribute_units)
        handler = ff.get_parameter_handler(potential.type)

        for key, value in zip(potential.parameter_keys, potential.parameters.detach()):
            smirks = key.id
            # skip virtual particles
            if "EP" in smirks:
                continue

            parameter = handler[smirks]
            for index, col in enumerate(potential.parameter_cols):
                if col == "epsilon":
                    val = value[index].item() * unit.kilocalories_per_mole
                    # val = value[index].item() * potential.attribute_units[index]
                elif col == "sigma":
                    val = value[index].item() * unit.angstrom
                else:
                    val = value[index].item() * potential.attribute_units[index]

                
                setattr(parameter, col, val)

    output_forcefield = input_directory / "output.offxml"
    ff.to_file(str(output_forcefield))
    print(f"Force field written to {output_forcefield}")


if __name__ == "__main__":
    main()
