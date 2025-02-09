import typing
import warnings
import click

import pandas as pd
import numpy as np
import tqdm

import MDAnalysis as mda

def convert_to_au(kcal: float) -> float:
    from openff.units import unit

    return (kcal * unit.kilocalorie).m_as(unit.hartree) / int(unit.avogadro_number)

def system_to_target(
    df: pd.DataFrame,
    system_id: int,
    output_directory: str = ".",
    energy_columns: list[str] = ["cbs_CCSD(T)_all"]
):
    import pathlib
    from openff.toolkit.topology.molecule import Molecule, unit
    
    df2 = df[df.system_id == system_id].sort_values("k_index")

    assert len(df2["mapped_smiles0"].unique()) == 1
    assert len(df2["mapped_smiles1"].unique()) == 1

    offmol1 = Molecule.from_mapped_smiles(
        df2["mapped_smiles0"].values[0],
        allow_undefined_stereo=True
    )
    offmol2 = Molecule.from_mapped_smiles(
        df2["mapped_smiles1"].values[0],
        allow_undefined_stereo=True
    )

    target_name = f"interaction-energy-{system_id}"
    IGNORE_PATTERNS = ["[#1:1]~[#1:2]"]
    for pattern in IGNORE_PATTERNS:
        if offmol1.chemical_environment_matches(pattern) or offmol2.chemical_environment_matches(pattern):
            warnings.warn(f"Skipping {target_name} due to {pattern}")
            return

    directory = pathlib.Path(output_directory) / target_name
    directory.mkdir(exist_ok=True, parents=True)

    subdf = pd.DataFrame(df2)
    conformers1 = []
    conformers2 = []
    all_coordinates = []

    for _, row in subdf.iterrows():
        xyz0 = np.array(row["xyz0"]).reshape((-1, 3))
        xyz1 = np.array(row["xyz1"]).reshape((-1, 3))
        conformers1.append(xyz0 * unit.angstrom)
        conformers2.append(xyz1 * unit.angstrom)
        all_coordinates.append(np.concatenate([xyz0, xyz1]))

    # xyz_text = [list(map(float, x.split())) for x in subdf["xyz"].values]
    # coordinates = np.array(xyz_text)
    # shape = (len(subdf), offmol1.n_atoms + offmol2.n_atoms, 3)
    # coordinates = coordinates.reshape(shape)

    # coords1 = coordinates[0, :offmol1.n_atoms, :] * unit.angstrom
    offmol1._conformers = [conformers1[0]]
    molfile1 = directory / "fragment1.mol2"
    offmol1.to_file(str(molfile1), "MOL2")
    
    # coords2 = coordinates[0, -offmol2.n_atoms:, :] * unit.angstrom
    offmol2._conformers = [conformers2[0]]
    molfile2 = directory / "fragment2.mol2"
    offmol2.to_file(str(molfile2), "MOL2")
    
    u1 = mda.Universe(offmol1.to_rdkit())
    u1.add_TopologyAttr("resids")
    u1.residues.resids = 1
    
    u2 = mda.Universe(offmol2.to_rdkit())
    u2.add_TopologyAttr("resids")
    u2.residues.resids = 2
    u = mda.Merge(u1.atoms, u2.atoms)

    # u.load_new(coordinates)
    u.load_new(np.array(all_coordinates))
    u.dimensions = None
    
    pdbfile = directory / "all.pdb"
    with mda.Writer(str(pdbfile), n_atoms=u.atoms.n_atoms) as writer:
        for ts in u.trajectory:
            writer.write(u.atoms)
        
    with pdbfile.open("r") as file:
        lines = [
            x.strip()
            for x in file.readlines()
            if not x.startswith("CRYST") and not x.startswith("REMARK")
        ]
    with pdbfile.open("w") as file:
        file.write("\n".join(lines))
        
    qdatafile = directory / "qdata.txt"
    with qdatafile.open("w") as file:
        for _, row in df2.iterrows():
            file.write(f"LABEL {row['k_index']}\n")
            # qdata.txt expects AU
            energy = 0
            for energy_column in energy_columns:
                energy += convert_to_au(row[energy_column])
            file.write(f"INTERACTION {energy}\n")
    return u


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
)
@click.option(
    "--output",
    "output_directory",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
)
@click.option(
    "--energy-column",
    "energy_columns",
    type=str,
    default=["cbs_CCSD(T)_all"],
    multiple=True
)
def convert_all(
    input_path: str,
    output_directory: str = "targets",
    energy_columns: list[str] = ["cbs_CCSD(T)_all",]
):
    import pyarrow.dataset as ds
    
    dataset = ds.dataset(input_path)
    df = dataset.to_table().to_pandas()
    i = 0
    for system_id in tqdm.tqdm(df.system_id.unique()):
        system_to_target(
            df,
            system_id,
            output_directory,
            energy_columns=energy_columns,
        )
        i += 1

    print(f"Converted {i} systems")


if __name__ == "__main__":
    convert_all()