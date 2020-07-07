from CoLoRe_analysis.data_treatment import data_treatment
import numpy as np
from shutil import rmtree
import os

import logging
log = logging.getLogger(__name__)

def redshift_to_str_for_path(redshift):
    return round(float(redshift)*100)

# The class shear reader is used to get data from data_treatment, it will always be shear information but it can also treat with cl information.
class ShearReader:
    def __init__(self,location):
        self.location = location
    
    def do_data_treatment(self,source=1, do_cls=False, do_kappa=False, minz=None, maxz=None, output_path=None):
        log.info(f'Doing data treatment for source: { source }. cls: { do_cls }, kappa: { do_kappa }, minz: { minz }, maxz: { maxz }')
        data_treatment(self.location,source, do_cls, do_kappa, minz, maxz, output_path)

    def get_values(self, parameter, source=1, minz=None, maxz=None, do_cls=False, do_kappa=False, compute=False):
        log.info(f'Getting values for sim: { self.location }. Parameter: { parameter }')
        if minz != None and maxz != None:
            minz_str    = redshift_to_str_for_path(minz)
            maxz_str    = redshift_to_str_for_path(maxz)
            path    = self.location + f'/data_treated/binned/{ str(minz_str) }_{ str(maxz_str) }/source_{ source }'
        else:
            path    = self.location + f'/data_treated/source_{ source }'

        try:
            return np.loadtxt( path + '/'+parameter+'.dat')
        except OSError:
            if not compute:
                raise

            if parameter == 'mp_k': 
                do_kappa = True
            if parameter[:2] == 'cl' or parameter == 'ld' or parameter == 'lt':
                do_cls   = True

            self.do_data_treatment(source=source, do_cls=do_cls, do_kappa=do_kappa, minz=minz, maxz=maxz, output_path=path)
            return np.loadtxt( path + '/'+parameter+'.dat')

    
    def compute_binned_statistics(self, minz, maxz, bins, source=1, do_cls=False, do_kappa=False):
        log.info(f'Computing binned statistics for sim: { self.location }')
        # I use mp_e1 to not compute if values already exist
        step = (maxz-minz)/bins
        for b in range(bins):
            _ = self.get_values('mp_e1', minz=minz+b*step, maxz= minz + (1+b)*step, do_cls=do_cls, do_kappa=do_kappa, source=source, compute=True)
    
    def remove_data_treated(self):
        log.info(f'Removing treated data for sim: { self.location }')
        if os.path.isdir(self.location + '/data_treated'):
            rmtree(self.location + '/data_treated')