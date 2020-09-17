import sys, os
import sys
sys.path.insert(1,'..')
from CoLoRe_analysis.shear_reader import ShearReader
from CoLoRe_analysis.sims_reader import (FileManager, Sim0404)
import shutil
from CoLoRe_analysis.compute_data_shear import compute_data_shear
from multiprocessing import Pool

import logging.config
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

def log_error(retval):
    print('Error:',retval)

path = "/global/cscratch1/sd/cramirez/CoLoRe_LSST/"

filt = {
    "status" : ["done"],
    "template": ["shear_test"],
    "factor" : [0]
}

def main():
    sims = {}
    for i, sim in enumerate(FileManager.get_simulations(path,filt)):
        simname = i
        sims[simname] = Sim0404(sim, simname)
        print(f'Id. { simname }\tLocation: { sims[simname].location }')

    compute_data_shear_args = []


    for sim in sims.values():
        log.info(f'Computing information for sim in locations: { sim.location }')
        # if not os.path.isdir(sim.location + '/pred_lj'):
        #     shutil.copytree('/global/cscratch1/sd/cramirez/CoLoRe_LSST/templates/shear_test/pred_lj',sim.location + '/pred_lj')

        sim.set_shear_reader()
        sim.shear_reader.remove_shear_data()
        
        for b in range(10):
            minz = 0 + b*0.25
            maxz = 0 + (1+b)*0.25
            minz_str    = round(float(minz)*100)
            maxz_str    = round(float(maxz)*100)
            arguments = (sim.location, 2,False,True,minz,maxz,sim.location+ f'/shear_data/binned/{ str(minz_str) }_{ str(maxz_str) }/source_2')

            compute_data_shear_args.append(arguments)
        #sim.shear_reader.compute_binned_statistics(minz=0, maxz=2.5, bins=10, source=2, do_cls=False, do_kappa=True)

    pool = Pool(processes = 64)
    
    x= [pool.apply_async(compute_data_shear, args, error_callback=log_error) for args in compute_data_shear_args]

    pool.close()
    pool.join()

    [p.get() for p in x]

if __name__ == '__main__':
    main()

