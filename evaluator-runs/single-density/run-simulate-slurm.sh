#!/usr/bin/env bash
#SBATCH -J simulate
#SBATCH --array=1-5
#SBATCH -p standard
#SBATCH -t 5-00:00:00
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1gb
#SBATCH --account XXX
#SBATCH --output slurm-%x.%A-%a.out

. ~/.bashrc

# Use the right conda environment
conda activate evaluator-test-env

WATER="tip3p"

REP="${SLURM_ARRAY_TASK_ID}"
PORT="813${REP}"
echo $PORT

REPDIR="rep${REP}"

mkdir $REPDIR

cp *.py dataset.json $REPDIR/

cd $REPDIR

python simulate-slurm.py -n 1000 -w $WATER -p $PORT



