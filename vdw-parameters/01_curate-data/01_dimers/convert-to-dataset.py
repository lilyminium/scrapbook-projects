import contextlib
import itertools
import logging
import math
import typing

import click
from click_option_group import optgroup

import tqdm
import numpy as np

from openff.evaluator.utils.checkmol import (
    ChemicalEnvironment,
    analyse_functional_groups,
)

logger = logging.getLogger(__name__)


def assign_functional_groups(smiles: str) -> typing.List[str]:
    groups = analyse_functional_groups(smiles)
    if smiles == "O" and groups is None:
        return ["Aqueous"]
    if groups is None:
        return []
    return sorted(gp.value for gp in groups)


def single_convert(row):
    entry = dict(row)
    xyz = np.array(
        list(map(float, entry.pop("xyz").split()))
    ).reshape((-1, 3))
    xyz0 = xyz[: entry["natoms0"]]
    xyz1 = xyz[entry["natoms0"] :]
    entry["xyz0"] = xyz0.flatten().tolist()
    entry["xyz1"] = xyz1.flatten().tolist()

    fg0 = assign_functional_groups(row["smiles0"])
    entry["functional_groups0"] = fg0
    fg1 = assign_functional_groups(row["smiles1"])
    entry["functional_groups1"] = fg1
    combinations = set()
    for f0 in fg0:
        for f1 in fg1:
            x, y = sorted([f0, f1])
            combinations.add(f"{x} + {y}")
    entry["functional_groups_combinations"] = sorted(combinations)
    return entry

def batch_convert(rows):
    entries = []
    for _, row in tqdm.tqdm(rows):
        entries.append(single_convert(row))
    return entries


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
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
def main(
    input_path: str,
    output_path: str,
    worker_type: typing.Literal["lsf", "local"] = "local",
    queue: str = "cpuqueue",
    conda_environment: str = "openff-nagl",
    memory: int = 4,  # GB
    walltime: int = 32,  # hours
    batch_size: int = 300,
    n_workers: int = -1,
):
    import pandas as pd
    import pyarrow as pa
    import pyarrow.dataset as ds

    from openff.nagl.utils._parallelization import batch_distributed
    from dask import distributed

    df = pd.read_csv(input_path)
    all_rows = list(df.iterrows())
    entries = []

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
        futures = list(batcher(batch_convert))
        for i, future in tqdm.tqdm(
            enumerate(distributed.as_completed(futures, raise_errors=False)),
            total=len(futures),
            desc="Saving rows",
        ):
            entries.extend(future.result())
    
    table = pa.Table.from_pylist(entries)
    ds.write_dataset(table, output_path, format="parquet")



if __name__ == "__main__":
    main()
