#!/bin/bash -l
#SBATCH --job-name=genclimo
#SBATCH --output=<outDir>/genclimo.o%j
#SBATCH --account=<account>
#SBATCH --nodes=1
#SBATCH --time=<wallMin>
#SBATCH --qos=<partition>
#SBATCH --constraint=cpu

source <source>
# user-defined environment
python <genclimoDir>/genclimo.py -c <case> -s <start> -e <end> -indir <directory> -outdir <outDir> -m <model> -v <vars> -t <time>
