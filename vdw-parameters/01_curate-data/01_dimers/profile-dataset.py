from collections import Counter
import click
import tqdm


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Input dataset",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    help="Output CSV"
)
def main(
    input_path: str,
    output_path: str,
):
    import pandas as pd
    import pyarrow.dataset as ds

    dataset = ds.dataset(input_path)
    rows = dataset.to_table(
        columns=["functional_groups_combinations"]
    ).to_pydict()["functional_groups_combinations"]

    counter = Counter()
    for row in tqdm.tqdm(rows):
        for fg_combination in row:
            counter[fg_combination] += 1
    
    entries = []
    for k in sorted(counter):
        entries.append({
            "Combination": k,
            "Count": counter[k]
        })

    df = pd.DataFrame(entries)
    df.to_csv(output_path)
    print(f"Wrote to {output_path}")



if __name__ == "__main__":
    main()
