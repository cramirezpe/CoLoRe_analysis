from CoLoRe_analysis.compute_data_CCL import compute_data
import numpy as np
from shutil import rmtree
import os
import json

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

    def do_data_computations(self, source=1, output_path=None, nside=128, max_files=None, downsampling=1, zbins=[-1,0.15,1], nz_h = 50, nz_min=0, nz_max=None):
        '''Computes the Cls from CCL and for the sim.

        Args:
            source (int, optional): CoLoRe output source to use as input (default: 1)
            output_path (str, optional): Set the output path (default: { sim_path }/ccl_data/source_{ source }/)
        '''
        log.info(f'Computing data for source: { source }')
        compute_data(self.location, source, output_path, nside, None, downsampling, zbins, nz_h, nz_min, nz_max)

    def get_values(self, value, **kwargs):
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
            kwargs (): Parameters for the ccl script. The full list is given at help(do_data_computations)

        Returns:
            Array of desired value. Raises an exception if the compute option is set to False but the value was not computed. 
        '''
        matched_sims = self.search_output(**kwargs)
        if len(matched_sims) == 0:
            while True:
                confirmation = input('Simulation with the given parameters does not exist. Do you want to compute it? (y/n)?')
                if confirmation == 'y':
                    self.do_data_computations(**kwargs)
                    return self.get_values(value, **kwargs)
                elif confirmation == 'n':
                    break

        elif len(matched_sims) == 1: 
            id_ = matched_sims[0]['id']
            return np.loadtxt(self.location + f'/ccl_data/{id_}/{ value }.dat')

        elif len(matched_sims) > 1:
            print('Multiple simulations does exist with the given parameters:')
            for x in matched_sims:
                print(x)
            return matched_sims

    def search_output(self, **kwargs):
        ''' Searches into the output directory to see if any of the outputs saved matches the data dictionary given as input. This data dictionary consists in the arguments given to the function do_data_computations.
    
        Args:
            **kwargs: Parameters of the simulations that we want to match (they should be parameters given in the self.do_data_computations function).

        Returns:
            List of dicts with the info of each run.
        '''

        if not os.path.isdir(self.location + f'/ccl_data'): 
            return []

        ids = [f.name for f in os.scandir(self.location + f'/ccl_data') if f.is_dir()]

        if len(ids) == 0: 
            return []

        compatible = []
        for id_ in sorted(ids):
            try:
                with open(f'{self.location}/ccl_data/{id_}/INFO.json') as json_file:
                    data = json.load(json_file)
                    for key in kwargs.keys():
                        if kwargs[key] != data[key]:
                            break
                    else: 
                        compatible.append(data)

            except FileNotFoundError:
                pass
        
        return compatible

    def remove_computed_data(self):
        while True:
            confirmation = input(f'Remove all computed ccl data from sim {self.location}? (y/n)')
            if confirmation == 'y':
                print('Removing all computed data')
                if os.path.isdir(self.location + '/ccl_data'):
                    rmtree(self.location + '/ccl_data')
                break
            
            elif confirmation == 'n': # pragma: no cover
                print('Cancelling')
                return

