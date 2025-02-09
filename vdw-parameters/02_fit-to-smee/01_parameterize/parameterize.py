"""Apply OpenFF 2.1.0 parameters to each unique molecule in the data set."""
import functools
import multiprocessing
import pathlib

import openff.interchange
import openff.toolkit
import smee
import smee.converters
import torch
import tqdm

import click


def build_interchange(
    smiles: str, force_field_paths: tuple[str, ...]
) -> openff.interchange.Interchange | None:
    forcefield = openff.toolkit.ForceField(*force_field_paths, allow_cosmetic_attributes=True)
    handler = forcefield.get_parameter_handler("vdW")
    print(handler.parameters[-2:])
    try:
        return openff.interchange.Interchange.from_smirnoff(
            forcefield,
            openff.toolkit.Molecule.from_mapped_smiles(
                smiles, allow_undefined_stereo=True
            ).to_topology(),
        )
    except BaseException as e:
        print(f"failed to parameterize {smiles}: {e}")
        return None


def apply_parameters(
    unique_smiles: list[str], *force_field_paths: str
) -> tuple[smee.TensorForceField, dict[str, smee.TensorTopology]]:
    
    interchanges = []
    # for smiles in tqdm.tqdm(unique_smiles):
    #     interchanges.append(
    #         build_interchange(smiles, force_field_paths)
    #     )


    build_interchange_fn = functools.partial(
        build_interchange, force_field_paths=force_field_paths
    )

    with multiprocessing.get_context("spawn").Pool() as pool:
        interchanges = list(
            tqdm.tqdm(
                pool.imap(build_interchange_fn, unique_smiles),
                total=len(unique_smiles),
                desc="building interchanges",
            )
        )

    unique_smiles, interchanges = zip(
        *[(s, i) for s, i in zip(unique_smiles, interchanges) if i is not None]
    )

    force_field, topologies = smee.converters.convert_interchange(interchanges)

    return force_field, {
        smiles: topology for smiles, topology in zip(unique_smiles, topologies)
    }


@click.command()
@click.option(
    "--input-smee-dataset",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to the input SMEE dataset.",
)
@click.option(
    "--forcefield",
    type=str,
    help="Path to the force field to apply.",
    default="openff-2.1.0.offxml",
)
@click.option(
    "--output-file",
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    help="Path to the output file.",
)
def main(
    input_smee_dataset: str,
    output_file: str,
    forcefield: str = "openff-2.1.0.offxml",
):
    import datasets

    # load dataset
    ds = datasets.Dataset.load_from_disk(input_smee_dataset)
    unique_smiles = set(ds["smiles_a"])
    unique_smiles |= set(ds["smiles_b"])
    

    print(f"N smiles={len(unique_smiles)}", flush=True)

    unique_smiles = sorted(unique_smiles)

    print(f"Applying {forcefield}")

    force_field, topologies = apply_parameters(unique_smiles, forcefield)
    torch.save((force_field, topologies), output_file)
    print(f"saved to {output_file}", flush=True)


if __name__ == "__main__":
    main()
