#!/bin/bash
#SBATCH -J set-up-fit
#SBATCH -p free
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=96gb
#SBATCH --account ...
#SBATCH --output slurm-%x.%A.out

# ===================== conda environment =====================
source ~/.bashrc
conda activate fit-virtual-sites-tk010-py39-fb-dimers

DATASET_NAME="ccsdt-mapped-filtered-des370k-training"
# DATASET_NAME="ccsdt-mapped-neutral-filtered-des370k-training"
# DATASET_NAME="ccsdt-mapped-attractive-filtered-des370k-training"
# DATASET_NAME="ccsdt-mapped-attractive-neutral-filtered-des370k-training"
FORCEFIELD_NAME="openff_unconstrained-2.1.0"
FORCEFIELD_NAME="openff_unconstrained-2.1.0_n2r5"
FORCEFIELD_NAME="openff_unconstrained-2.1.0_n3-r5-X4"

DATASET_DIRECTORY="../../01_curate-data/01_dimers/output/targets"
DATASET="${DATASET_DIRECTORY}/${DATASET_NAME}"
FORCEFIELD="../../forcefields/input/${FORCEFIELD_NAME}.offxml"
OUTPUT_DIRECTORY="output/${DATASET_NAME}_${FORCEFIELD_NAME}"

echo $OUTPUT_DIRECTORY

python set-up-fit.py                        \
    --port              55350               \
    --forcefield        $FORCEFIELD         \
    --input             $DATASET            \
    --output            $OUTPUT_DIRECTORY


cp -r $DATASET "${OUTPUT_DIRECTORY}/targets"
cp submit_hpc3_worker_local.sh hpc3_master.sh "${OUTPUT_DIRECTORY}/"

cd $OUTPUT_DIRECTORY
tar -czvf targets.tar.gz targets
