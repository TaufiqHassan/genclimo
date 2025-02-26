#!/bin/bash -l
#SBATCH --job-name=pyclimo
#SBATCH --output=<outDir>/climopy.o%j
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --time=<wallMin>
#SBATCH --partition=<partition>

source /share/apps/E3SM/conda_envs/base/etc/profile.d/conda.sh
conda activate <env>
python <pyclimoDir>/pyclimo.py -c <case> -s <start> -e <end> -dir <directory> -dir2 <outDir> -m <model> -v <vars> -t <time>
