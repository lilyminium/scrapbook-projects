# Density

## Property

- Property type: Density (see dataset.json for full specification, details pulled out below)
- Substance: CCCC
- Temperature: 298.15 K
- Pressure: 101.325 kPa
- Value: 0.62089 g/mL

Number of molecules in this example: 1000

## Steps

Links to the code as implemented in Evaluator, and to the output files / directory where the protocol is executed, are provided for each step.

### Packing the box

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/coordinates.py#L24)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_build_coordinates)

Packmol is used to pack the box of liquid (1000 molecules, here).
`output.pdb` contains the packed box.

The box is packed to a default density of 0.95 g/mL with a 2 A tolerance in the box allowed. The box size to pack is [approximated from the mass density](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/utils/packmol.py#L109) and scaled up by 1.1. 

### Assign parameters

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/forcefield.py#L530)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_assign_parameters)

Parameters are assigned from the OFFXML force field. The output is an OpenMM System XML file. 

### Energy minimisation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L325)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_energy_minimisation)

The packmol box is minimised in OpenMM. A simulation is built using the OpenMM system in the parameter assignment step, and the PDB in the packmol step. The minimised file is `minimised.pdb`.

### Equilibration simulation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L366)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_equilibration_simulation)

The minimised coordinates are used in equilibration (NPT, 200 ps, 2 fs timestep).
The output file is `output.pdb`. 

- integrator: LangevinMiddleIntegrator
- barostat: MonteCarloBarostat
- steps: 100000
- output frequency: every 5000 steps
- time step: 2 fs

### Production simulation

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/openmm.py#L366)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_conditional_group/6316_production_simulation)

A production simulation is carried out for data collection.
This is in a group called "conditional_group" because you can
add conditions for convergence (e.g. within a particular error).
In this run, there are no conditions, only a single 2 ns simulation is carried out.
This is what was done in the Sage 2.0 workflow.

- integrator: LangevinMiddleIntegrator
- barostat: MonteCarloBarostat
- number of steps: 1000000
- time step: 2 fs
- output_frequency: every 2000 steps

A number of observables are collected during the simulation, including the density which is extracted in the next step.

### Analysis protocol

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/protocols/analysis.py#L337)

[Directory link](working-directory/SimulationLayer/757f586ad95d4b919916bd85661a60de/6316_conditional_group/6316_average_density)

The density of the simulation is extracted. Here also, the time series statistics are computed, i.e. the frame indices used to grab uncorrelated frames of data to compute each observable.

The error shown here is the standard error by bootstrapping the sampled uncorrelated data for an estimated distribution of means.

Density: 0.6021266425136393 ± 0.00025317782022733087 g/mL

#### Time series statistics

[Evaluator link](https://github.com/openforcefield/openff-evaluator/blob/main/openff/evaluator/utils/timeseries.py#L19)

This is in the `*output.json` of the `average_density` directory. The details of each computation can be found in `timeseries.py` as linked above, but the algorithm is drawn from `pymbar`. The `n_total_points` is the total number of samples available; `n_uncorrelated_points` is the number of data points which are uncorrelated; `equilibration_index` is the index after which the time series is considered equilibrated.

- n_total_points (total frames in the trajectory): 500
- n_uncorrelated_points (total uncorrelated frames): 237
- statistical_inefficiency: 1.0018478264299615
- equilibration_index: 26


### Decorrelated observables

The uncorrelated observables used to compute each average observable. (Links not provided as the observable of interest, density, is already calculated in the analysis protocol).

### Decorrelated trajectory

The uncorrelated frames of the trajectory used to compute each average observable. (Links not provided as trajectory probably not of interest).
