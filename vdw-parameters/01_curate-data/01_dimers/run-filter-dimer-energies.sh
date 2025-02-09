#!/usr/bin/env bash
#SBATCH -J filter-dimer-energies
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

python filter-dimer-energies-parameterizable.py     \
    --n-workers                     300                     \
    --worker-type                   "slurm"                 \
    --batch-size                    300                     \
    --memory                        4                       \
    --walltime                      480                     \
    --queue                         "free"                  \
    --conda-environment             "openff-nagl-test"      \
    --input     "input/Donchev et al DES370K.csv"   \
    --output    "input/filtered-des370k.csv"        \
    --no-neutral-only    

