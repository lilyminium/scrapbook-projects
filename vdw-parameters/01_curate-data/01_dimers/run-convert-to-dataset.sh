#!/usr/bin/env bash
#SBATCH -J convert-to-dataset
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
conda activate openff-evaluator

conda env export > convert-dataset-env.yaml

python convert-to-dataset.py                \
    --n-workers                     300                     \
    --worker-type                   "slurm"                 \
    --batch-size                    200                     \
    --memory                        4                       \
    --walltime                      480                     \
    --queue                         "free"                  \
    --conda-environment             "openff-evaluator"      \
    --input     "input/mapped-filtered-des370k.csv"        \
    --output    "input/mapped-filtered-des370k"

