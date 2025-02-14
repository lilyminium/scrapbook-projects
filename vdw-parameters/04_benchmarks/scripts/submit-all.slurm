#!/usr/bin/env bash
#SBATCH -J submit
#SBATCH --array=1-10
#SBATCH -p standard
#SBATCH -t 48:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16gb
#SBATCH --account XX
#SBATCH --output run-logs/slurm-%x.%A-%a.out

. ~/.bashrc

# NAME="openff-2.1.0"
# NAME="no-vsites_n2r-vdw_hmix-only"
NAME="vsites-v3_n2r-vdw-dimers_hmix-only-v2"

# Use the right conda environment
conda activate openff-sage

export OE_LICENSE=/home/lilywang/oe_license.txt

echo $SLURM_ARRAY_TASK_ID

PADDED_NUMBER=$(printf "%03d" $SLURM_ARRAY_TASK_ID)
ENTRY_NAME="entry-${PADDED_NUMBER}"
echo $ENTRY_NAME

OUTPUT_DIRECTORY="output/split_${NAME}/output/${ENTRY_NAME}"
cd $OUTPUT_DIRECTORY

conda env export > conda_env.yaml

# Run the commands
# only run if results.json doesn't already exist
if [ ! -f results.json ]; then
    nonbonded benchmark run --restart true
fi

echo "done"
