#!/usr/bin/env bash
#SBATCH -J evaluate
#SBATCH -p free-gpu
#SBATCH --gres=gpu:1
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account dmobley_lab_gpu
#SBATCH --output slurm-%x.%A.out

. ~/.bashrc

conda activate evaluator-vsites-hfes-0.3

DATASET_FILE="../filtered_dataset_sfe_np1.json"
FORCEFIELD_FILE="force-field.json"

SUBDIRECTORY="test-opc"
SUBDIRECTORY="test-opc3"

cd $SUBDIRECTORY

python ../evaluate-property.py                          \
    --input         ../filtered_dataset_sfe_np1.json    \
    --output        results.json                        \
    --forcefield    force-field.json                    \
    --port          9013
