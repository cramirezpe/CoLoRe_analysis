import unittest
import pickle
from CoLoRe_analysis.compute_data_CCL import compute_data
import numpy as np
import os

from shutil import rmtree

class TestComputeDataCCL(unittest.TestCase):
    sim_path    = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/New_CCL'
    output_path = sim_path + '/ccl_data/source_1'

    def tearDown(self):
        if os.path.isdir(self.output_path):
            rmtree(self.output_path)

    def test_normal_output_data(self):
        with open(self.sim_path+ '/all_data.pkl','rb') as input:
            target_values = pickle.load(input) 
            
        np.random.seed(1)
        compute_data(self.sim_path)

        values = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_mm_d', 'cl_mm_t']

        for i, value in enumerate(values):
            np.testing.assert_equal(target_values[i], np.loadtxt(self.output_path + f'/{value}.dat'))

    