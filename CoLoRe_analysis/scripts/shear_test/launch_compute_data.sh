#!/bin/bash

#SBATCH -J $job_name
#SBATCH -C haswell
#SBATCH --partition=debug
#SBATCH --account=desi
#SBATCH --nodes=1
#SBATCH --time=30
#SBATCH --error=runs/compute_data.error
#SBATCH --output=runs/compute_data.out

rm -r runs
mkdir runs
export OMP_NUM_THREADS=1
source activate colore_env
umask 0002
command="python compute_data.py"

$command &> runs/terminal_out.log
