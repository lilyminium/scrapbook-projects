import click
from click_option_group import optgroup

import typing

import multiprocessing
import pandas as pd
import tqdm



@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(exists=False, file_okay=True, dir_okay=True),
)
@click.option(
    "--column",
    "column_name",
    type=str,
    default="cbs_CCSD(T)_all",
    help="The column to filter",
)
@click.option(
    "--max-energy",
    "max_energy",
    type=float,
    help="The maximum energy to keep",
)
def filter(
    column_name: str,
    max_energy: float,
    output_path: str,
    input_path: str,
):
    import pyarrow.dataset as ds
    import pyarrow.compute as pc

    dataset = ds.dataset(input_path)
    print(dataset.schema)

    expression = pc.field(column_name) <= max_energy
    subset = dataset.filter(expression)
    ds.write_dataset(subset, output_path, format="parquet")

    n_original = dataset.count_rows()
    n_filtered = subset.count_rows()

    print(f"Filtered {n_original - n_filtered} rows")
    print(f"Original length: {n_original}")
    print(f"Filtered length: {n_filtered}")

    print(f"Wrote to {output_path}")


if __name__ == "__main__":
    filter()