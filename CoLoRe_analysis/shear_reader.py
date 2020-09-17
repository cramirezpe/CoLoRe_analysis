from CoLoRe_analysis.compute_data_shear import compute_data_shear
import numpy as np
from shutil import rmtree
import os

import logging
log = logging.getLogger(__name__)

def redshift_to_str_for_path(redshift):
    return round(float(redshift)*100)

# The class shear reader is used to get data from compute_data_shear, it will always be shear information but it can also deal with cl information.
class ShearReader:
    def __init__(self, sim_location, analysis_location):
        self.sim_location = sim_location
        self.analysis_location = analysis_location
    
    def do_compute_data_shear(self, source=1, do_cls=False, do_kappa=False, minz=None, maxz=None, output_path=None):
        log.info(f'Doing shear data computation for source: { source }. cls: { do_cls }, kappa: { do_kappa }, minz: { minz }, maxz: { maxz }')
        compute_data_shear(self.sim_location, source, do_cls, do_kappa, minz, maxz, output_path)

    def get_values(self, parameter, source=1, minz=None, maxz=None, do_cls=False, do_kappa=False, compute=False):
        log.info(f'Getting values for sim: { self.sim_location }. Parameter: { parameter }')
        if minz != None and maxz != None:
            minz_str    = redshift_to_str_for_path(minz)
            maxz_str    = redshift_to_str_for_path(maxz)
            path    = self.analysis_location + f'/shear_data/binned/{ str(minz_str) }_{ str(maxz_str) }/source_{ source }'
        else:
            path    = self.analysis_location + f'/shear_data/source_{ source }'

        try:
            return np.loadtxt( path + '/'+parameter+'.dat')
        except OSError:
            if not compute:
                raise

            if parameter == 'mp_k': 
                do_kappa = True
            if parameter[:2] == 'cl' or parameter == 'ld' or parameter == 'lt':
                do_cls   = True

            self.do_compute_data_shear(source=source, do_cls=do_cls, do_kappa=do_kappa, minz=minz, maxz=maxz, output_path=path)
            return np.loadtxt( path + '/'+parameter+'.dat')

    
    def compute_binned_statistics(self, minz, maxz, bins, source=1, do_cls=False, do_kappa=False):
        log.info(f'Computing binned statistics for sim: { self.sim_location }')
        # I use mp_e1 to not compute if values already exist
        step = (maxz-minz)/bins
        for b in range(bins):
            _ = self.get_values('mp_e1', minz=minz+b*step, maxz= minz + (1+b)*step, do_cls=do_cls, do_kappa=do_kappa, source=source, compute=True)
    
    def remove_shear_data(self):
        while True:
            confirmation = input(f'Remove all shear data from sim {self.sim_location}? (y/n)')
            if confirmation == 'y':
                log.info(f'Removing shear data for sim: { self.sim_location }')
                if os.path.isdir(self.analysis_location + '/shear_data'):
                    rmtree(self.analysis_location + '/shear_data')
                break
            elif confirmation == 'n':
                print('Cancelling')
                return