#!/usr/bin/env bash
#SBATCH -J profile-dataset
#SBATCH --array=0-3
#SBATCH -p free
#SBATCH -t 16:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=24gb
#SBATCH --account ...
#SBATCH --output slurm-%x.%A-%a.out

# ===================== conda environment =====================
source ~/.bashrc
conda activate openff-nagl-test

NAMES=(
    "mapped-filtered-des370k"
    "mapped-attractive-filtered-des370k"
    "mapped-neutral-filtered-des370k"
    "mapped-attractive-neutral-filtered-des370k"
)

NAME=${NAMES[${SLURM_ARRAY_TASK_ID}]}

echo $NAME

python profile-dataset.py               \
    --input         "input/${NAME}"     \
    --output        "profiles/fg-${NAME}.csv"
