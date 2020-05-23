import sys, os
from lib.shear_reader import ShearReader
from lib.time_analysis_LSST import (FileManager, Sim0404)
import shutil

import logging.config
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

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

for sim in sims.values():
    log.info(f'Computing information for sim in locations: { sim.location }')
    # if not os.path.isdir(sim.location + '/pred_lj'):
    #     shutil.copytree('/global/cscratch1/sd/cramirez/CoLoRe_LSST/templates/shear_test/pred_lj',sim.location + '/pred_lj')

    sim.set_shear_reader()
    sim.shear_reader.remove_data_treated()
    sim.shear_reader.compute_binned_statistics(minz=0, maxz=2.5, bins=10, source=2, do_cls=False, do_kappa=True)