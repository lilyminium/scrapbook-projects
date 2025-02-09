#!/bin/bash
#SBATCH -J fit-to-dimers
#SBATCH --array=0-2
#SBATCH -p free
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32gb
#SBATCH --account ...
#SBATCH --output slurm-%x.%A-%a.out

# ===================== conda environment =====================
source ~/.bashrc
conda activate smee-descent-dev

DATASET_DIRECTORY="../../01_curate-data/01_dimers/output/descent"
PARAMETERIZED_DIRECTORY="../01_parameterize/output"

DATASET_NAMES=(
    "ccsdt-mapped-filtered-des370k-training"
    "ccsdt-mapped-neutral-filtered-des370k-training"
    "ccsdt-mapped-attractive-filtered-des370k-training"
    "ccsdt-mapped-attractive-neutral-filtered-des370k-training"
)
DATASET_NAME=${DATASET_NAMES[$SLURM_ARRAY_TASK_ID]}

# FORCEFIELD_NAME="openff_unconstrained-2.1.0"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n2r5"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n3-r5-X4"
FORCEFIELD_NAME="openff_unconstrained-2.1.0_n3-r5-X4b"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n4-r5-X4b-X2+"
# FORCEFIELD_NAME="openff_unconstrained-2.1.0_n5-r5-X4b-X2+-sub"

DATASET_PATH="${DATASET_DIRECTORY}/${DATASET_NAME}"
SYSTEM_NAME="${DATASET_NAME}_${FORCEFIELD_NAME}"
PARAMETERIZED_PATH="${PARAMETERIZED_DIRECTORY}/${SYSTEM_NAME}.pt"
INPUT_FORCE_FIELD="../../forcefields/input/${FORCEFIELD_NAME}.offxml"
OUTPUT_FORCE_FIELD="../../forcefields/output/smee-${SYSTEM_NAME}.offxml"

PORT=$((29600 + $SLURM_ARRAY_TASK_ID))

OUTPUT_DIRECTORY="output/${SYSTEM_NAME}"

echo $OUTPUT_DIRECTORY

python fit-to-dimers-smee.py                        \
    --port                  $PORT                   \
    --input-force-field     $INPUT_FORCE_FIELD      \
    --output                $OUTPUT_DIRECTORY       \
    --dataset               $DATASET_PATH           \
    --parameterized-ff      $PARAMETERIZED_PATH     \
    --lr                    0.001

cp "${OUTPUT_DIRECTORY}/force-field.offxml" $OUTPUT_FORCE_FIELD
