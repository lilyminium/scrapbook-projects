# like plot_torsions, but produce one plot per record matching a given
# parameter and include all of the individual interactions

import argparse
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import MDAnalysis as mda
import openmm
import openmm.unit
import pandas as pd
import qcelemental
from openff.units import unit
from openff.interchange.operations.minimize import (
    _DEFAULT_ENERGY_MINIMIZATION_TOLERANCE,
)
from openff.qcsubmit.results import TorsionDriveResultCollection
from openff.toolkit import ForceField, Molecule
from openff.units.openmm import from_openmm
from yammbs.analysis import get_rmsd

import tqdm


plt.style.use("seaborn-v0_8-colorblind")
pd.set_option("display.max_columns", None)

HARTREE2KCALMOL = qcelemental.constants.hartree2kcalmol


parser = argparse.ArgumentParser()
parser.add_argument("--forcefield", "-f", default="new-tm-2.2.offxml")
parser.add_argument("--pid", "-p", default="t72h")
parser.add_argument("--skip", "-s", action="store_true")


def minimize_constrained(ic, dihedral):
    "Return the optimized geometry of ic"

    simulation = ic.to_openmm_simulation(
        openmm.LangevinMiddleIntegrator(
            293.15 * openmm.unit.kelvin,
            1.0 / openmm.unit.picosecond,
            2.0 * openmm.unit.femtosecond,
        ),
        combine_nonbonded_forces=False,
    )

    simulation.context.computeVirtualSites()

    # constrained dihedral
    for i in dihedral:
        simulation.system.setParticleMass(i, 0.0)

    simulation.minimizeEnergy(
        tolerance=_DEFAULT_ENERGY_MINIMIZATION_TOLERANCE.to_openmm(),
        maxIterations=10_000,
    )

    coordinates = from_openmm(
        simulation.context.getState(getPositions=True).getPositions(
            asNumpy=True
        )[
            : ic.positions.shape[0],
            :,
        ],
    )
    return coordinates


def minimize_restrained(ic, dihedral, val, res):
    "Return the optimized geometry of ic"

    restraints = []
    restraint = openmm.PeriodicTorsionForce()
    i, j, k, ll = dihedral
    restraint.addTorsion(
        i,
        j,
        k,
        ll,
        1,  # periodicity
        # phase -- we want the minimum to be at val
        180 * openmm.unit.degrees + val,
        res * openmm.unit.kilojoules_per_mole,  # k
    )
    restraints.append(restraint)

    simulation = ic.to_openmm_simulation(
        openmm.LangevinMiddleIntegrator(
            293.15 * openmm.unit.kelvin,
            1.0 / openmm.unit.picosecond,
            2.0 * openmm.unit.femtosecond,
        ),
        combine_nonbonded_forces=False,
        additional_forces=restraints,
    )

    simulation.context.computeVirtualSites()

    simulation.minimizeEnergy(
        tolerance=_DEFAULT_ENERGY_MINIMIZATION_TOLERANCE.to_openmm(),
        maxIterations=10_000,
    )

    coordinates = from_openmm(
        simulation.context.getState(getPositions=True).getPositions(
            asNumpy=True
        )[
            : ic.positions.shape[0],
            :,
        ],
    )
    return coordinates


def get_dihedral(mol: Molecule, coords, dihedral):
    mol = Molecule(mol)
    mol._conformers = None
    mol.add_conformer(coords)
    u = mda.Universe(mol.to_rdkit())
    return u.atoms[list(dihedral)].dihedral.value()


def normalized_dihedral_difference(dihedral_1, dihedral_2):
    # MDAnalysis ranges from [-180, 180]
    diff = abs(dihedral_1 - dihedral_2)
    return min(diff, abs(360 - diff))


def _write_pdb(molecule, coordinates, filename):
    mol = Molecule(molecule)
    mol._conformers = [coordinates]
    mol.to_file(f"pdbs/{filename}", "PDB")

def main():
    args = parser.parse_args()

    ff = ForceField(args.forcefield)
    dataset = TorsionDriveResultCollection.parse_file("single-record.json")
    records_and_molecules = dataset.to_records()
    assert len(records_and_molecules) == 1
    qcrecord, molecule = records_and_molecules[0]
    molecule._conformers = None

    all_labels = ff.label_molecules(molecule.to_topology())[0]
    dihedral = next(
        indices
        for indices, parameter in all_labels["ProperTorsions"].items()
        if parameter.id == args.pid
    )
    parameter = all_labels["ProperTorsions"][dihedral]

    print(f"Dihedral: {dihedral}")

    a1 = list(dihedral[:3])
    a2 = list(dihedral[1:])
    print(f"Angle {a1}: eq value {all_labels['Angles'][a1].angle}")
    print(f"Angle {a2}: eq value {all_labels['Angles'][a2].angle}")


    rmsds = defaultdict(dict)
    dihedrals = defaultdict(dict)
    for grid_id in tqdm.tqdm(
            sorted(qcrecord.minimum_optimizations),
            desc="Iterating over grid points"
    ):
        optimization = qcrecord.minimum_optimizations[grid_id]
        grid_id = tuple(grid_id)[0]
        conformer = (optimization.final_molecule.geometry * unit.bohr).to(unit.angstrom)
        mol = Molecule(molecule)
        mol._conformers = [conformer]
        _write_pdb(mol, conformer, f"original_{grid_id}.pdb")

        # minimize constrained
        minimized = minimize_constrained(
            ff.create_interchange(mol.to_topology()), dihedral
        )
        _write_pdb(mol, minimized, f"constrained_{grid_id}.pdb")
        rmsd = get_rmsd(molecule, reference=conformer, target=minimized)
        rmsds["Constrained"][grid_id] = rmsd

        original_dihedral_value = get_dihedral(molecule, conformer, dihedral)
        minimized_dihedral_value = get_dihedral(molecule, minimized, dihedral)
        diff = original_dihedral_value - minimized_dihedral_value
        dihedrals["Constrained"][grid_id] = normalized_dihedral_difference(
            original_dihedral_value, minimized_dihedral_value
        )


        # minimize restrained
        for restraint in [0, 100, 1000, 100000]:
            minimized = minimize_restrained(
                ff.create_interchange(mol.to_topology()),
                dihedral,
                original_dihedral_value * openmm.unit.degrees,
                restraint,
            )
            _write_pdb(mol, minimized, f"restrained-{restraint}_{grid_id}.pdb")
            rmsd = get_rmsd(molecule, reference=conformer, target=minimized)
            rmsds[f"Res{restraint}"][grid_id] = rmsd

            minimized_dihedral_value = get_dihedral(molecule, minimized, dihedral)

            diff = original_dihedral_value - minimized_dihedral_value
            dihedrals[f"Res{restraint}"][grid_id] = normalized_dihedral_difference(
                original_dihedral_value, minimized_dihedral_value
            )


    df = pd.DataFrame.from_dict(rmsds)
    df.to_csv("rmsds.csv")

    df.plot()
    plt.title(f"{args.pid}\n{parameter.smirks}")
    plt.xlabel("Torsion Angle (deg)")
    plt.ylabel("RMSD (Å)")
    plt.savefig("rmsds.png", bbox_inches="tight", dpi=300)

    plt.close()

    df = pd.DataFrame.from_dict(dihedrals)
    df.to_csv("dihedral_differences.csv")
    print(df)
    df.plot()
    plt.xlabel("Torsion Angle (deg)")
    plt.ylabel("Δ Dihedral (deg)")
    plt.savefig("tors.png", bbox_inches="tight", dpi=300)


if __name__ == "__main__":
    main()
