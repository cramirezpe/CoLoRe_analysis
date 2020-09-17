#!/bin/bash

#SBATCH -J CoLoRe_LSST
#SBATCH -C haswell
#SBATCH --partition=debug
#SBATCH --account=desi
#SBATCH --nodes=10
#SBATCH --time=30
#SBATCH --error=%x-%j.error
#SBATCH --output=%x-%j.out

# This batch script will run CoLoRe with its original configuration on a given path. It is made to work with the new LSST simulations that should be carried out. 

export OMP_NUM_THREADS=64

cd /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110

sed -i "s#status= prepared#status= running#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
command="srun -N 10 -C haswell -c 64 -A desi /global/homes/c/cramirez/Codes/CoLoRe/CoLoRe param.cfg"
echo $command
$command > script/terminal_CoLoRe_LSST_${SLURM_JOBID}.log

if [ $? = 0 ]; then
	sed -i "s#status= running#status= done#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
else
	sed -i "s#status= running#status= crashed#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
fi

cd /global/homes/c/cramirez/Shs/CoLoRe_compute_data_shear
if [ 0 = 1 ];then
	echo "doing shear data computation"
	sed -i "s#status= done#status= running shear data computation#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
	python3 compute_data_shear_1run.py -p /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110
	if [ $? = 0 ]; then
		sed -i "s#status= running shear data computation#status= done#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
	else
		sed -i "s#status= running shear data computation#status= crashed on shear data computation#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200416090110/sim_info.dat
	fi
fi


