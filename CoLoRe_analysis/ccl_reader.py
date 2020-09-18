import json
import logging
import os
from shutil import rmtree

import numpy as np

from CoLoRe_analysis import compute_data_CCL

log = logging.getLogger(__name__)

class CCLReader:
    '''Class made to handle QA tests using CCL theoretical values'''

    def __init__(self, sim_location, analysis_location):
        '''Inits the class with a sim path

        Args: 
            sim_location (str): Path to the simulation
            analysis_location (str): Path to the analysis of the simulation
        '''
        self.sim_location = sim_location
        self.analysis_location = analysis_location

    def do_data_computations(self, source=1, nside=128, max_files=None, downsampling=1, zbins=[-1,0.15,1], nz_h = 50, nz_min=0, nz_max=None, **kwargs):
        '''Computes the Cls from CCL and for the sim.

        Args:
            source (int, optional): CoLoRe output source to use as input (default: 1)
            output_path (str, optional): Set the output path (default: { analysis_path }/ccl_data/{datetime}/
        '''
        log.info(f'Computing data for source: { source }')

        compute_data_CCL.compute_data(self.sim_location, self.analysis_location, source, nside, None, downsampling, zbins, nz_h, nz_min, nz_max, **kwargs)

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
            return np.loadtxt(self.analysis_location + f'/ccl_data/{id_}/{ value }.dat')

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

        if not os.path.isdir(self.analysis_location + f'/ccl_data'): 
            return []

        ids = [f.name for f in os.scandir(self.analysis_location + f'/ccl_data') if f.is_dir()]

        if len(ids) == 0: 
            return []

        compatible = []
        for id_ in sorted(ids):
            try:
                with open(f'{self.analysis_location}/ccl_data/{id_}/INFO.json') as json_file:
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
            confirmation = input(f'Remove all computed ccl data from sim {self.sim_location}? (y/n)')
            if confirmation == 'y':
                print('Removing all computed data')
                if os.path.isdir(self.analysis_location + '/ccl_data'):
                    rmtree(self.analysis_location + '/ccl_data')
                break
            
            elif confirmation == 'n': # pragma: no cover
                print('Cancelling')
                return
