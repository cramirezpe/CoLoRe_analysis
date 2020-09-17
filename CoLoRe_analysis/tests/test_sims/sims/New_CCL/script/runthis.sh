#!/bin/bash

#SBATCH -J CoLoRe_CCL
#SBATCH -C haswell
#SBATCH --partition=debug
#SBATCH --account=desi
#SBATCH --nodes=1
#SBATCH --time=15
#SBATCH --error=%x-%j.error
#SBATCH --output=%x-%j.out

# This batch script will run CoLoRe with its original configuration on a given path. It is made to work with the new LSST simulations that should be carried out. 

export OMP_NUM_THREADS=64

cd /global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/New/1/20200708_174453

sed -i "s#status = prepared#status = running#g" /global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/New/1/20200708_174453/sim_info.INI
command="srun -N 1 -C haswell -c 64 -A desi /global/homes/c/cramirez/Codes/CoLoRe/CoLoRe_0707/CoLoRe_New/CoLoRe param.cfg"
echo $command
$command > script/terminal_CoLoRe_CCL_${SLURM_JOBID}.log

if [ $? = 0 ]; then
	sed -i "s#status = running#status = done#g" /global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/New/1/20200708_174453/sim_info.INI
else
	sed -i "s#status = running#status = crashed#g" /global/cscratch1/sd/cramirez/CoLoRe_CCL/sims/New/1/20200708_174453/sim_info.INI
fi

