from CoLoRe_analysis.compute_data_CCL import compute_data
import numpy as np
from shutil import rmtree
import os

import logging
log = logging.getLogger(__name__)

class CCLReader:
    '''Class made to handle QA tests using CCL theoretical values'''

    def __init__(self, location):
        '''Inits the class with a sim path

        Args: 
            location (str): Path to the simulation
        '''
        self.location = location

    def do_data_computations(self, source=1, output_path=None):
        '''Computes the Cls from CCL and for the sim.

        Args:
            source (int, optional): CoLoRe output source to use as input (default: 1)
            output_path (str, optional): Set the output path (default: { sim_path }/ccl_data/source_{ source }/)
        '''
        log.info(f'Computing data for source: { source }')
        compute_data(self.location, source, output_path)

    def get_values(self, value, source=1, compute=False):
        '''Obtain values for Cls (CCL or sim)

        Args:
            value (str): Value we want to obtain. The possible values are: 
                pairs: pairs 
                shotnoise:
                nz_tot:
                z_nz:
                cld_dd_d:
                cl_dd_t:
                cl_dm_d:
                cl_dm_t:
                cl_mm_d:
                cl_mm_t:
            source (int, optional): CoLoRe output used as input (default: 1)
            compute (bool, optional): Whether to compute the values if they are not available or not (default: False)

        Returns:
            Array of desired value. Raises an exception if the compute option is set to False but the value was not computed. 
        '''
        path = self.location + f'/ccl_data/source_{ source }'

        try:
            return np.loadtxt( f'{ path }/{ value }.dat')
        except OSError:
            if not compute:
                raise
            self.do_data_computations(source=source, output_path=path)
            return np.loadtxt(f'{ path }/{ value }.dat')

    def remove_computed_data(self):
        if os.path.isdir(self.location + '/ccl_data'):
            rmtree(self.location + '/ccl_data')
