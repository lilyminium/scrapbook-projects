# Benchmarks

This contains physical property benchmarks, curated from ThermoML.

## Scripts

The results here were computed with a fairly old Python 3.9 environment and Simon's nonbonded library to execute. This is not strictly necessary, so I've also added an additional script that reads in a `dataset.json` and computes a property, which would work with modern Evaluator.

### Old scripts

1. `set-up-split.py` splits up each property into its own directory
2. `submit-all.slurm` executes each property with the `nonbonded` library

### New scripts

`simulate-slurm.py` simulates a single dataset of multiple properties.