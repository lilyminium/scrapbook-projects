#!/usr/bin/env bash
#SBATCH -J convert-to-targets
#SBATCH --array=1-3
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
    "mapped-filtered-des370k-training"
    "mapped-neutral-filtered-des370k-training"
    "mapped-attractive-filtered-des370k-training"
    "mapped-attractive-neutral-filtered-des370k-training"
)

NAME=${NAMES[${SLURM_ARRAY_TASK_ID}]}

echo $NAME

python convert-to-targets.py                        \
    --input             "splits/${NAME}"            \
    --energy-column     "cbs_CCSD(T)_all"           \
    --output            "output/targets/ccsdt-${NAME}"

