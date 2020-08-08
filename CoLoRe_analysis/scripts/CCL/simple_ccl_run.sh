#!/bin/bash -l

#SBATCH --partition debug
#SBATCH --nodes 1
#SBATCH --time 00:30:00
#SBATCH --job-name CoLoRe_CCL
#SBATCH --error=%x-%j.error
#SBATCH --output=%x-%j.out
#SBATCH -C haswell
#SBATCH -A desi

umask 0002
export OMP_NUM_THREADS=64
source activate colore_env

date
srun -n 1 -c 64 CoLoRe_compute_shear_CCL --paths /global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/New/0.1/20200729_130230 --zbins 0 1 80 --nz_h 100 --nz_min 0 --nz_max 2.5
date