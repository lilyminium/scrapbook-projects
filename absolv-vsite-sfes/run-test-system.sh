#!/usr/bin/env bash
#SBATCH -J test
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

conda activate absolv-dev


WATER="opc"
WATER="opc3"


mkdir $WATER
cd $WATER

python ../test-system.py --forcefield "openff-2.2.0.offxml" --forcefield "${WATER}.offxml"
