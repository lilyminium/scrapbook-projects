#!/usr/bin/env bash
#SBATCH -J set-up-split
#SBATCH -p free
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account XX
#SBATCH --output slurm-%x.%A.out

source ~/.bashrc
conda activate openff-sage

# export OE_LICENSE="~/oe_license.txt"

DATASET="thermoml-small"

FORCEFIELD_NAME="openff-2.1.0"

OUTPUT_DIRECTORY="output/${DATASET}/split_${FORCEFIELD_NAME}/output"

python set-up-split.py                                                      \
    --forcefield        "../forcefields/v3/${FORCEFIELD_NAME}.offxml"       \
    --dataset           "input/${DATASET}.json"           \
    --output-directory  $OUTPUT_DIRECTORY               \
    --computer          hpc3                            \
    --environment       openff-sage                     \
    --port              9000
