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

cd /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717

sed -i "s#status= prepared#status= running#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
command="srun -N 10 -C haswell -c 64 -A desi /global/homes/c/cramirez/Codes/faster_shear_0404/CoLoRe_New/CoLoRe param.cfg"
echo $command
$command > script/terminal_CoLoRe_LSST_${SLURM_JOBID}.log

if [ $? = 0 ]; then
	sed -i "s#status= running#status= done#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
else
	sed -i "s#status= running#status= crashed#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
fi

cd /global/homes/c/cramirez/Shs/CoLoRe_data_treatment
if [ 0 = 1 ];then
	echo "doing data treatment"
	sed -i "s#status= done#status= running data treatment#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
	python3 storedata-scratch-full-path-1run.py -p /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717
	if [ $? = 0 ]; then
		sed -i "s#status= running data treatment#status= done#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
	else
		sed -i "s#status= running data treatment#status= crashed on data treatment#g" /global/cscratch1/sd/cramirez/CoLoRe_LSST/New/shear_20/nside_512/0.0001/202004160717/sim_info.dat
	fi
fi


