#!/bin/bash

#SBATCH -J $job_name
#SBATCH -C haswell
#SBATCH --partition=debug
#SBATCH --account=desi
#SBATCH --nodes=1
#SBATCH --time=30
#SBATCH --error=runs/compute_correlations.error
#SBATCH --output=runs/compute_correlations.out

rm -r runs/*
export OMP_NUM_THREADS=1
source activate colore_env
umask 0002
command="python compute_regressions.py"

$command > runs/terminal_out_regressions.log
