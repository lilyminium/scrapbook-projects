import pathlib

from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.client import RequestOptions
from openff.evaluator.client import EvaluatorClient, ConnectionOptions


data_set_path = "small-test-set.json"

data_set = PhysicalPropertyDataSet.from_json(data_set_path)
from openff.evaluator.forcefield import SmirnoffForceFieldSource

force_field_path = "openff-1.0.0.offxml"
force_field_source = SmirnoffForceFieldSource.from_path(force_field_path)
from openff.evaluator.properties import Density, EnthalpyOfVaporization

density_schema = Density.default_simulation_schema(n_molecules=256)
for schema in density_schema.workflow_schema.protocol_schemas:
    # equilibration_simulation is a Protocol                                                                                                                                
    if "simulation" in schema.id:
        schema.inputs[".steps_per_iteration"] = 10
        schema.inputs[".output_frequency"] = 10
    # conditional_group is a group of protocols                                                                                                                             
    if "conditional" in schema.id:
        for protocol_name, protocol in schema.protocol_schemas.items():
            if "simulation" in protocol_name:
                protocol.inputs[".steps_per_iteration"] = 10
                protocol.inputs[".output_frequency"] = 10


# Create an options object which defines how the data set should be estimated.                                                                                              
estimation_options = RequestOptions()
# Specify that we only wish to use molecular simulation to estimate the data set.                                                                                           
estimation_options.calculation_layers = ["SimulationLayer"]

# Add our custom schemas, specifying that the should be used by the 'SimulationLayer'                                                                                       
estimation_options.add_schema("SimulationLayer", "Density", density_schema)

connection_options = ConnectionOptions()
evaluator_client = EvaluatorClient(
    connection_options=connection_options
)

request, exception = evaluator_client.request_estimate(
    property_set=data_set,
    force_field_source=force_field_source,
    options=estimation_options,
)
assert exception is None

results, exception = request.results(synchronous=True, polling_interval=30)
assert exception is None
print(len(results.queued_properties))

print(len(results.estimated_properties))

print(len(results.unsuccessful_properties))
print(len(results.exceptions))
print(results.estimated_properties.json("estimated_data_set.json", format=True))