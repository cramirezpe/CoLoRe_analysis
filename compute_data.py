import sys, os
from lib.shear_reader import ShearReader
from lib.time_analysis_LSST import (FileManager, Sim0404)
import shutil
from lib.data_treatment import data_treatment
from multiprocessing import Pool

import logging.config
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

def log_error(retval):
    print('Error:',retval)

path = "/global/cscratch1/sd/cramirez/CoLoRe_LSST/"

filt = {
    "status" : ["done"],
    "template": ["master_with_shear"],
    "factor": [0.1,0.01]
}

sims = {}
for i, sim in enumerate(FileManager.get_simulations(path,filt)):
    simname = i
    sims[simname] = Sim0404(sim, simname)
    print(f'Id. { simname }\tLocation: { sims[simname].location }')

data_treatment_args = []


for sim in sims.values():
    log.info(f'Computing information for sim in locations: { sim.location }')
    # if not os.path.isdir(sim.location + '/pred_lj'):
    #     shutil.copytree('/global/cscratch1/sd/cramirez/CoLoRe_LSST/templates/shear_test/pred_lj',sim.location + '/pred_lj')

    sim.set_shear_reader()
    sim.shear_reader.remove_data_treated()
    
    for b in range(10):
        minz = 0 + b*0.25
        maxz = 0 + (1+b)*0.25
        minz_str    = round(float(minz)*100)
        maxz_str    = round(float(maxz)*100)
        arguments = (sim.location, 2,False,True,minz,maxz,sim.location+ f'/data_treated/binned/{ str(minz_str) }_{ str(maxz_str) }/source_2')

        data_treatment_args.append(arguments)
    #sim.shear_reader.compute_binned_statistics(minz=0, maxz=2.5, bins=10, source=2, do_cls=False, do_kappa=True)

if __name__ == '__main__':
    pool = Pool(processes = 64)
    
    x= [pool.apply_async(data_treatment, args, error_callback=log_error) for args in data_treatment_args]

    pool.close()
    pool.join()

    [p.get() for p in x]

