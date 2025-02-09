#!/usr/bin/env bash
#SBATCH -J split-dataset
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

NAME="mapped-filtered-des370k"
# NAME="mapped-neutral-filtered-des370k"
# NAME="mapped-attractive-filtered-des370k"
# NAME="mapped-attractive-neutral-filtered-des370k"

echo $NAME

python split-dataset.py                             \
    --input     "input/${NAME}"                     \
    --validation-fraction 0.2                       \
    --output-prefix    "splits/${NAME}"
