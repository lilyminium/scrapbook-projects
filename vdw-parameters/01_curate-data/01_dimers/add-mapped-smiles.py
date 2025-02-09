import typing
import warnings
import click
from click_option_group import optgroup

import pandas as pd
import numpy as np
import tqdm

import MDAnalysis as mda
from rdkit import Chem

def create_xyz_string(
    n_atoms: int,
    elements: list[str],
    xyz: np.ndarray,
) -> str:
    lines = [f"{n_atoms}", ""]
    for el, (x, y, z) in zip(elements, xyz):
        lines.append(f"{el:>2} {x:>10.8f} {y:>10.8f} {z:>10.8f}")
    return "\n".join(lines)

def convert_to_au(kcal: float) -> float:
    from openff.units import unit

    return (kcal * unit.kilocalorie).m_as(unit.hartree) / int(unit.avogadro_number)

def get_mapped_smiles(
    reference_smiles: str,
    elements: list[str],
    xyz: np.ndarray,
) -> str:
    import io
    from openff.toolkit.topology import Molecule

    ref = Molecule.from_smiles(reference_smiles, allow_undefined_stereo=True)
    
    xyz_string = create_xyz_string(ref.n_atoms, elements, xyz)
    u = mda.Universe(io.StringIO(xyz_string), format="xyz")
    u.add_TopologyAttr("elements", elements)
    u.add_TopologyAttr("types", elements)
    u.atoms.types = [x.upper() for x in u.atoms.types]  # bug in guessing code...

    # manually convert some tricky ones
    PATTERNS = {
        "BrC(Br)Br": "[H:5][C:2]([Br:3])([Br:1])[Br:4]",
        "BrCCBr": "[H:5][C:2]([Br:1])([H:6])[C:3]([H:7])([H:8])[Br:4]",
        "CCBr": "[H:7][C:2]([Br:3])([H:8])[C:1]([H:4])([H:5])[H:6]",
        "BrCBr": "[H:4][C:2]([Br:1])([Br:3])[H:5]",
        "CBr": "[H:3][C:1]([Br:2])([H:4])[H:5]",
        "CC(Br)Br": "[H:8][C:2]([Br:4])([C:1]([H:5])([H:6])[H:7])[Br:3]",
        "CSSC": "[C:1]([S:2][S:3][C:4]([H:8])([H:9])[H:10])([H:5])([H:6])[H:7]",
        "ICCI": "[I:1][C:2]([C:3]([I:4])([H:7])[H:8])([H:5])[H:6]",
        "CI": "[H:3][C:1]([I:2])([H:4])[H:5]",
        "ICI": "[H:4][C:2]([I:1])([I:3])[H:5]",
        "CSCC": "[H:10][C:4]([H:11])([H:12])[C:3]([H:8])([H:9])[S:2][C:1]([H:6])([H:5])[H:7]",
        "CC(I)I": "[H:8][C:2]([I:3])([I:4])[C:1]([H:5])([H:6])[H:7]",
        "CCI": "[H:7][C:2]([I:3])([H:8])[C:1]([H:4])([H:5])[H:6]",
        "CSCCO": "[H:6][C:1]([H:7])([H:8])[S:2][C:3]([H:9])([H:10])[C:4]([H:11])([H:12])[O:5][H:13]",
    }

    try:
        rdmol = u.atoms.convert_to("RDKIT")
    except AttributeError:
        try:
            rdmol = u.atoms.convert_to("RDKIT", force=True)
        except ValueError:
            raise ValueError(reference_smiles)
        xyzmol = Molecule.from_rdkit(rdmol, allow_undefined_stereo=True)
        # warnings.warn(
        # print(
        #     "Could not convert xyz to rdkit. "
        #     f"Reference smiles: {reference_smiles} ."
        #     f"Converted smiles: {xyzmol.to_smiles()}"
        # )
        for ref_smi, mapped in PATTERNS.items():
            if reference_smiles == ref_smi:
                xyzmol = Molecule.from_mapped_smiles(
                    mapped,
                    allow_undefined_stereo=True
                )

        is_iso, mapping = Molecule.are_isomorphic(
            ref,
            xyzmol,
            return_atom_map=True,
            bond_order_matching=False,
            formal_charge_matching=True,
            aromatic_matching=False
        )
        assert is_iso, f"Could not convert. Reference smiles: {reference_smiles} . Converted smiles: {xyzmol.to_smiles()}"
    else:
        if "SS" in reference_smiles: #and "." in Chem.MolToSmiles(rdmol):
            rwmol = Chem.RWMol(rdmol)
            s_atoms = []
            for atom in rwmol.GetAtoms():
                if atom.GetAtomicNum() == 16 and atom.GetFormalCharge() == -1:
                    s_atoms.append(atom.GetIdx())
            if len(s_atoms) == 2:
                rwmol.AddBond(s_atoms[0], s_atoms[1], Chem.BondType.SINGLE)
                rwmol.GetAtomWithIdx(s_atoms[0]).SetFormalCharge(0)
                rwmol.GetAtomWithIdx(s_atoms[1]).SetFormalCharge(0)
            Chem.SanitizeMol(rwmol)
            rdmol = Chem.Mol(rwmol)
            print("RDKit smiles", Chem.MolToSmiles(rdmol))

        xyzmol = Molecule.from_rdkit(rdmol, allow_undefined_stereo=True)
        is_iso, mapping = Molecule.are_isomorphic(ref, xyzmol, return_atom_map=True)

        if not is_iso:
            # warnings.warn(
            # print(
            #     "Could not convert xyz to isomorphic rdkit. "
            #     f"Reference smiles: {reference_smiles} ."
            #     f"Converted smiles: {xyzmol.to_smiles()}"
            # )
            is_iso, mapping = Molecule.are_isomorphic(
                ref,
                xyzmol,
                return_atom_map=True,
                bond_order_matching=False,
                formal_charge_matching=True,
                aromatic_matching=False
            )

            if not is_iso:  # charges may have been normalised weirdly
                for ref_smi, mapped in PATTERNS.items():
                    if reference_smiles == ref_smi:
                        xyzmol = Molecule.from_mapped_smiles(
                            mapped,
                            allow_undefined_stereo=True
                        )

                is_iso, mapping = Molecule.are_isomorphic(
                    ref,
                    xyzmol,
                    return_atom_map=True,
                    bond_order_matching=False,
                    formal_charge_matching=False,
                    aromatic_matching=False,
                    atom_stereochemistry_matching=False,
                    bond_stereochemistry_matching=False,
                )

                assert is_iso, f"Could not convert. Reference smiles: {reference_smiles} . Converted smiles: {xyzmol.to_smiles(mapped=True)}"
    offmol = ref.remap(mapping)
    try:
        off_elements = [atom.symbol for atom in offmol.atoms]
    except AttributeError:
        off_elements = [atom.element.symbol for atom in offmol.atoms]

    assert off_elements == list(elements)
    return offmol.to_smiles(mapped=True)


def row_to_mapped_smiles(row: dict[str, typing.Any]) -> dict[str, typing.Any]:
    import numpy as np
    
    elements = row["elements"].split()
    xyz = np.array(list(map(float, row["xyz"].split()))).reshape((-1, 3))

    natoms0 = row["natoms0"]
    natoms1 = row["natoms1"]
    assert len(xyz) == natoms0 + natoms1

    mapped1 = get_mapped_smiles(
        row["smiles0"],
        elements[:natoms0],
        xyz[:natoms0],
    )
    mapped2 = get_mapped_smiles(
        row["smiles1"],
        elements[natoms0:],
        xyz[natoms0:],
    )
    # row["mapped_smiles0"] = mapped1
    # row["mapped_smiles1"] = mapped2

    return (mapped1, mapped2)

    # return pd.Series(
    #     [mapped1, mapped2],
    #     index=["mapped_smiles0", "mapped_smiles1"]
    # )

def batch_row_to_mapped_smiles(indices_and_rows) -> list[tuple[int, str, str]]:
    results = []
    for index, row in tqdm.tqdm(indices_and_rows):
        result = (index, *row_to_mapped_smiles(row))
        results.append(result)
    return results

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
def add_mapped_smiles(
    input_file: str,
    output_file: str,
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

    all_results = []

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
            batcher(batch_row_to_mapped_smiles)
        )
        for i, future in tqdm.tqdm(
            enumerate(distributed.as_completed(futures, raise_errors=False)),
            total=len(futures),
            desc="Saving rows",
        ):
            all_results.extend(future.result())

    all_results = sorted(all_results)
    df["mapped_smiles0"] = [x[1] for x in all_results]
    df["mapped_smiles1"] = [x[2] for x in all_results]
    df.to_csv(output_file, index=False)


if __name__ == "__main__":
    add_mapped_smiles()