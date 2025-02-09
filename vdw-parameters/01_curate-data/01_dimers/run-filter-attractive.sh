#!/usr/bin/env bash
#SBATCH -J filter
#SBATCH -p free
#SBATCH -t 16:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=24gb
#SBATCH --account ...
#SBATCH --output slurm-%x.%A.out

# ===================== conda environment =====================
source ~/.bashrc
conda activate openff-nagl-test

conda env export > full-env.yaml

python filter-dimer-energies-threshold.py           \
    --input     "input/mapped-filtered-des370k"     \
    --output    "input/mapped-attractive-filtered-des370k"  \
    --max-energy 0.0

python filter-dimer-energies-charge.py              \
    --input     "input/mapped-filtered-des370k"     \
    --output    "input/mapped-neutral-filtered-des370k"  \
    --charge    0

python filter-dimer-energies-charge.py                              \
    --input     "input/mapped-attractive-filtered-des370k"          \
    --output    "input/mapped-attractive-neutral-filtered-des370k"  \
    --charge    0
