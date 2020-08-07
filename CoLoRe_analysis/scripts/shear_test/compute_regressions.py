import sys
sys.path.insert(1,'..')
from CoLoRe_analysis.correlations import CorrelateTwoShears
from CoLoRe_analysis.sims_reader import (Sim0404)
from CoLoRe_analysis.file_manager import FileManager
from multiprocessing import Pool

import logging.config
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

def do_correlation(corrTwoShearobj,minz,maxz):
    print('computing regression')
    corrTwoShearobj.store_regression(parameter='mp_e1', source=2, minz=minz, maxz=maxz)
    return

def log_error(retval):
    print('Error:',retval)

def log_result(retval):
    print('Result:',retval)

# create arguments
old_01_sim  = Sim0404('/global/cscratch1/sd/cramirez/CoLoRe_LSST/Old/shear_100/nside_512/0.1/20200524160256')
old_001_sim = Sim0404('/global/cscratch1/sd/cramirez/CoLoRe_LSST/Old/shear_100/nside_512/0.01/20200524164137')
master_01_sim = Sim0404('/global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.1/20200528034653')
master_001_sim = Sim0404('/global/cscratch1/sd/cramirez/CoLoRe_LSST/master/0.01/20200528012712')

# New sims:
filt = {
    "version" : ['New'],
    "status" : ["done"],
    "template": ["master_with_shear"],
    "factor" : [0.01,0.1],
    "shear" : [5,20,30,40,50,100],
    "nside" : [512,1024,2048],
    "commit" : "2005"
}


sims_01  = []
sims_001 = []

for i, sim in enumerate(FileManager.get_simulations('/global/cscratch1/sd/cramirez/CoLoRe_LSST/',filt)):
    sim = Sim0404(sim)
    if sim.factor == 0.01:
        sims_001.append(sim)
    elif sim.factor == 0.1:
        sims_01.append(sim)

corrobjs = []
for x in sims_01:
    print('0.1 sim at:\t',x.location)
    corrobjs.append(CorrelateTwoShears([x],[old_01_sim]))

for x in sims_001:
    print('0.01 sim at:\t',x.location)
    corrobjs.append(CorrelateTwoShears([x],[old_001_sim]))

corrobjs.append(CorrelateTwoShears([old_01_sim],[master_01_sim]))
corrobjs.append(CorrelateTwoShears([old_001_sim],[master_001_sim]))

data_treatment_args = []
for x in corrobjs:
    for b in range(10):
        minz= 0 + b*0.25
        maxz= 0 + (1+b)*0.25
        data_treatment_args.append((x, minz,maxz))

if __name__ == '__main__':
    pool = Pool(processes = 64)
    print('starting pool')
    x= [pool.apply_async(do_correlation, args,callback=log_result, error_callback=log_error) for args in data_treatment_args]

    pool.close()
    pool.join()
    print('closing pool')
    [print(p.get()) for p in x]




