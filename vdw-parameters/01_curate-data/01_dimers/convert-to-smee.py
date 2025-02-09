import pathlib
import click
import tqdm
import numpy as np
import pandas as pd
import torch

def convert_row_to_dimer(
    df: pd.DataFrame,
    system_id: int,
    energy_columns: list[str] = ["cbs_CCSD(T)_all"],
    name="DES370K",
):
    from descent.targets import dimers

    df2 = df[df.system_id == system_id].sort_values("k_index")
    subdf = pd.DataFrame(df2)

    coords = []
    energies = np.zeros(len(subdf))
    for i, (_, row) in enumerate(subdf.iterrows()):
        coords.append(
            np.concatenate([row["xyz0"], row["xyz1"]])
        )
        for column in energy_columns:
            energies[i] += row[column]
    coords = np.array(coords)
    
    dimer = dimers.Dimer(
        smiles_a=row["mapped_smiles0"],
        smiles_b=row["mapped_smiles1"],
        coords=torch.Tensor(coords),
        energy=torch.Tensor(energies),
        source=f"system={row['system_id']} orig={row['group_orig']} group={row['group_id']}"
    )
    return dimer


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
    import pandas as pd
    import pyarrow.dataset as ds
    from descent.targets import dimers

    output_directory = pathlib.Path(output_directory)
    output_directory.parent.mkdir(parents=True, exist_ok=True)

    dataset = ds.dataset(input_path)
    df = dataset.to_table().to_pandas()

    individual_dimers = []
    i = 0
    for system_id in tqdm.tqdm(df.system_id.unique()):
        dimer = convert_row_to_dimer(df, system_id, energy_columns=energy_columns)
        individual_dimers.append(dimer)
        i += 1
    
    print(f"Converted {i} systems")

    dimer_dataset = dimers.create_dataset(individual_dimers)
    dimer_dataset.save_to_disk(output_directory)

if __name__ == "__main__":
    convert_all()
