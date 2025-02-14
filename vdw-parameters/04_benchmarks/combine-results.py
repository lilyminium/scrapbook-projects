import pathlib
import tqdm
import click

from nonbonded.library.utilities.environments import ChemicalEnvironment

ANALYSIS_ENVIRONMENTS = [
    ChemicalEnvironment.Aqueous,
    ChemicalEnvironment.SecondaryAmine,
    ChemicalEnvironment.CarboxylicAcidSecondaryAmide,
    ChemicalEnvironment.AlkylBromide,
    ChemicalEnvironment.Alcohol,
    ChemicalEnvironment.Aromatic,
    ChemicalEnvironment.ArylChloride,
    ChemicalEnvironment.Thiol,
    ChemicalEnvironment.CarboxylicAcidTertiaryAmide,
    ChemicalEnvironment.AlkylChloride,
    ChemicalEnvironment.CarboxylicAcidEster,
    ChemicalEnvironment.Thiourea,
    ChemicalEnvironment.Acetal,
    ChemicalEnvironment.Thioether,
    ChemicalEnvironment.TertiaryAmine,
    ChemicalEnvironment.Ketone,
    ChemicalEnvironment.Disulfide,
    ChemicalEnvironment.Aldehyde,
    ChemicalEnvironment.PrimaryAmine,
    ChemicalEnvironment.Heterocycle,
    ChemicalEnvironment.Ether,
    ChemicalEnvironment.Alkene,
    ChemicalEnvironment.Alkane,
    ChemicalEnvironment.Sulfone,
]

@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(file_okay=True, dir_okay=False),
)
@click.option(
    "--reference",
    "reference_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "--benchmark",
    "benchmark_path",
    type=click.Path(file_okay=True, dir_okay=False),
)
def main(
    input_path: str,
    output_path: str,
    reference_path: str,
    benchmark_path: str,
):
    from openff.evaluator.client.client import RequestResult
    from openff.evaluator.datasets.datasets import PhysicalPropertyDataSet
    from nonbonded.library.models.results import BenchmarkResult
    from nonbonded.library.models.datasets import DataSet, DataSetCollection

    # Get the path to the directory
    path = pathlib.Path(input_path)

    # Get the list of files in the directory
    full = PhysicalPropertyDataSet()
    jsons = sorted(path.glob("entry-*/results.json"))
    for json in tqdm.tqdm(jsons):
        id_ = int(pathlib.Path(json).parent.stem.split("-")[1])
        with json.open("r") as f:
            result = RequestResult.parse_json(f.read())
        estimated = result.estimated_properties.properties
        estimated[0].id = str(id_)
        full._properties.extend(estimated)
    
    # Save the combined dataset
    full.json(output_path, format=True)
    print(f"Saved {len(full.properties)} properties to {output_path}")

    reference_ds = DataSet.parse_file(reference_path)
    for i, entry in enumerate(reference_ds.entries, 1):
        entry.id = str(i)
    reference = DataSetCollection(data_sets=[reference_ds])
    benchmark_result = BenchmarkResult.from_evaluator(
        project_id="na",
        study_id="na",
        benchmark_id="na",
        reference_data_set=reference,
        estimated_data_set=full,
        analysis_environments=ANALYSIS_ENVIRONMENTS
    )
    benchmark_result.to_file(benchmark_path)


if __name__ == "__main__":
    main()
