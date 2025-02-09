#!/bin/bash
#
#SBATCH -J parameterize
#SBATCH --array=0-3
#SBATCH -p free
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=8
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account ...
#SBATCH --output slurm-%x.%A-%a.out

# ===================== conda environment =====================
source ~/.bashrc
conda activate smee-descent-dev


DATASET_DIRECTORY="../../01_curate-data/01_dimers/output/descent"

DATASET_NAMES=(
    "ccsdt-mapped-filtered-des370k-training"
    "ccsdt-mapped-neutral-filtered-des370k-training"
    "ccsdt-mapped-attractive-filtered-des370k-training"
    "ccsdt-mapped-attractive-neutral-filtered-des370k-training"
)
DATASET_NAME=${DATASET_NAMES[$SLURM_ARRAY_TASK_ID]}

DATASET_PATH="${DATASET_DIRECTORY}/${DATASET_NAME}"

# FORCEFIELD_NAME="openff_unconstrained-2.1.0"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n2r5"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n3-r5-X4"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n3-r5-X4b"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n4-r5-X4b-X2+"
FORCEFIELD_NAME="openff_unconstrained-2.1.0_n5-r5-X4b-X2+-sub"

echo $DATASET_PATH


python parameterize.py                                      \
    --input-smee-dataset        $DATASET_PATH               \
    --forcefield                "../../forcefields/input/${FORCEFIELD_NAME}.offxml" \
    --output-file               "output/${DATASET_NAME}_${FORCEFIELD_NAME}.pt"


