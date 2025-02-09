from collections import Counter
import click


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Input dataset",
)
@click.option(
    "--validation-fraction",
    "validation_fraction",
    type=float,
    default=0.2,
    help="Fraction of dataset to use for validation",
)
@click.option(
    "--output-prefix",
    "output_prefix",
    type=str,
    help="Output prefix",
)
def main(
    input_path: str,
    validation_fraction: float,
    output_prefix: str,
):
    """
    Clumsily split dataset into training and validation sets.
    """
    import pyarrow.dataset as ds
    import pyarrow.compute as pc
    import pyarrow as pa

    dataset = ds.dataset(input_path)
    print(dataset.schema)
    columns = ["system_id", "functional_groups_combinations"]
    rows = []
    # get unique system ids
    for row in dataset.to_table(columns=columns).to_pylist():
        if row not in rows:
            rows.append(row)
    rows = sorted(
        rows,
        key=lambda x: len(x["functional_groups_combinations"]),
    )[::-1]

    n_validation = int(len(rows) * validation_fraction)
    n_training = len(rows) - n_validation

    training_systems = set()
    n_functional_groups = Counter()

    first = rows.pop(0)
    training_systems.add(first["system_id"])
    for fg_combination in first["functional_groups_combinations"]:
        n_functional_groups[fg_combination] += 1
    
    # first pass: ensure all groups are represented
    for row in rows:
        if any(
            n_functional_groups[fg_combination] == 0
            for fg_combination in row["functional_groups_combinations"]
        ):
            training_systems.add(row["system_id"])
            for fg_combination in row["functional_groups_combinations"]:
                n_functional_groups[fg_combination] += 1
    
    # second pass: select underrepresented groups
    rows = [
        row
        for row in rows
        if row["system_id"] not in training_systems
    ]
    while len(training_systems) < n_training:
        # select the row with the most underrepresented groups
        row = max(
            rows,
            key=lambda x: (
                0 if not len(x["functional_groups_combinations"]) else
                sum(
                    n_functional_groups[fg_combination]
                    for fg_combination in x["functional_groups_combinations"]
                ) / len(x["functional_groups_combinations"])
            ),
        )
        training_systems.add(row["system_id"])
        for fg_combination in row["functional_groups_combinations"]:
            n_functional_groups[fg_combination] += 1
        rows.remove(row)
    
    validation_systems = [row["system_id"] for row in rows]

    print(f"Training: {len(training_systems)}")
    print(f"Validation: {len(validation_systems)}")

    validation = dataset.filter(
        pc.field("system_id").isin(validation_systems)
    )
    training = dataset.filter(
        pc.field("system_id").isin(training_systems)
    )

    output_validation_path = f"{output_prefix}-validation"
    output_training_path = f"{output_prefix}-training"

    ds.write_dataset(validation, output_validation_path, format="parquet")
    ds.write_dataset(training, output_training_path, format="parquet")

    print(f"Wrote to {output_validation_path}")
    print(f"Wrote to {output_training_path}")
    

if __name__ == "__main__":
    main()
