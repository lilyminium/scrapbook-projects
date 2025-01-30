# Enthalpy of mixing

## Property

Property type: EnthalpyOfMixing (see dataset.json for full specification, details pulled out below)
Substance: 0.5098 O (component 0) + 0.4902 OCCN(CCO)CCO (component 1)
Temperature: 303.15 K
Pressure: 100 kPa
Value: -1.221 kJ/mol

Number of molecules in this example: 1000

Formula:

$$dH_{mixing} = H_{mixture} - (\chi_0 \times H_{component 0} + \chi_1 \times H_{component 1}) $$

## Steps

Links to the code as implemented in Evaluator, and to the output files / directory where the protocol is executed, are provided for each step.

### Packing the box

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/coordinates.py#L24)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_build_coordinates_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_build_coordinates_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_build_coordinates_mixture)

Packmol is used to pack boxes of each component and mixture with the appropriate number of molecules (1000, here).
`output.pdb` contains the packed box.
The `*output.json` files contains some information about the box that Evaluator
uses, such as the number of molecules and the *output* mole fraction.
This can differ from the input; while the input specifies the mole fractions
to 4 dp (0.5098 and 0.4902), as there are only 1000 molecules the mole fractions
are rounded to 3 dp (0.510 and 0.490).

### Assign parameters

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/forcefield.py#L530)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_assign_parameters_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_assign_parameters_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_assign_parameters_mixture)

Parameters are assigned from the OFFXML force field. The output is an OpenMM System XML file. 

### Energy minimisation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L325)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_energy_minimisation_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_energy_minimisation_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_energy_minimisation_mixture)

The packmol box is minimised in OpenMM. A simulation is built using the OpenMM system in the parameter assignment step, and the PDB in the packmol step. The minimised file is `minimised.pdb`.

### Equilibration simulation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L366)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_equilibration_simulation_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_equilibration_simulation_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_equilibration_simulation_mixture)


The minimised coordinates are used in equilibration (NPT, 200 ps, 2 fs timestep).
The output file is `output.pdb`. 

### Production simulation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L366)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_0/6421_production_simulation_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_1/6421_production_simulation_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_mixture/6421_production_simulation_mixture)

A production simulation is carried out for data collection.
This is in a group called "conditional_group" because you can
add conditions for convergence (e.g. within a particular error).
In this run, there are no conditions, only a single 2 ns simulation is carried out.
This is what was done in the Sage 2.0 workflow.

A number of observables are collected during the simulation, including the enthalpy which is extracted in the next step.

### Analysis protocol

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/analysis.py#L337)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_0/6421_extract_observable_component_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_1/6421_extract_observable_component_1)
- [mixture](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_mixture/6421_extract_observable_mixture)


The enthalpy of each simulation is extracted. Here also, the time series statistics are computed, i.e. the frame indices used to grab uncorrelated frames of data to compute each observable.

The error shown here is the standard error by bootstrapping the sampled uncorrelated data for an estimated distribution of means.

Enthalpy of water (component 0): -32.30838306619456 ± 0.015409825095665686 kJ/mol
Enthalpy of component 1: 261.5758490214179 ± 0.07449593325903951 kJ/mol
Enthalpy of mixture: 109.39961993636248 ± 0.07782841891809451 kJ/mol

#### Time series statistics

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/utils/timeseries.py#L19)

This is in the `*output.json` of the `extract_observable` directory. The details of each computation can be found in `timeseries.py` as linked above, but the algorithm is drawn from `pymbar`. The `n_total_points` is the total number of samples available; `n_uncorrelated_points` is the number of data points which are uncorrelated; `equilibration_index` is the index after which the time series is considered equilibrated.

For water (component 0):

- n_total_points (total frames in the trajectory): 500
- n_uncorrelated_points (total uncorrelated frames): 250
- statistical_inefficiency: 1.2481836418679895
- equilibration_index: 0

For triethanolamine (component 1):

- n_total_points (total frames in the trajectory): 500
- n_uncorrelated_points (total uncorrelated frames): 52
- statistical_inefficiency: 2.7860509152115225
- equilibration_index: 344

For the mixture:

- n_total_points (total frames in the trajectory): 500
- n_uncorrelated_points (total uncorrelated frames): 46
- statistical_inefficiency: 2.469177110617585
- equilibration_index: 364

#### Weighting by mole fraction

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/miscellaneous.py#L189)

Directory links:
- [component 0](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_0/6421_weight_by_mole_fraction_0)
- [component 1](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_conditional_group_component_1/6421_weight_by_mole_fraction_1)

The enthalpy of the individual components is weighted by the mole fraction of each in the mixture.

For water:

$$ \chi_0 \times H_{component 0} = 0.51 \times -32.30838306619456 $$
$$ \chi_0 \times H_{component 0} = -16.477275363759226 ± 0.0078590107987895 $$

For triethanolamine:

$$ \chi_1 \times H_{component 1} = 0.49 \times 261.5758490214179 $$
$$ \chi_1 \times H_{component 1} = 128.17216602049479 ± 0.03650300729692936 $$


### Decorrelated observables

The uncorrelated observables used to compute each average observable. (Links not provided as the observable of interest, enthalpy, is already calculated in the analysis protocol).

### Decorrelated trajectory

The uncorrelated frames of the trajectory used to compute each average observable. (Links not provided as trajectory probably not of interest).

### Final computation of enthalpy of mixing

The component enthalpies are added [here](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_add_component_observables):

$$ \chi_0 \times H_{component 0} + \chi_1 \times H_{component 1} = -16.477275363759226 + 128.17216602049479 $$
$$ \chi_0 \times H_{component 0} + \chi_1 \times H_{component 1} = 111.69489065673557 ± 0.03733943749516278 $$


The enthalpy of mixing is computed [here](working-directory/SimulationLayer/58e9a3d3eeef497394d8b29544a8730d/6421_calculate_excess_observable):

$$dH_{mixing} = H_{mixture} - (\chi_0 \times H_{component 0} + \chi_1 \times H_{component 1})$$
$$dH_{mixing} = 109.39961993636248 - 111.69489065673557$$
$$dH_{mixing} = -2.2952707203730824 ± 0.08632205039122727$$
