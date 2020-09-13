import unittest
import pickle
from CoLoRe_analysis.compute_data_CCL import compute_data
import numpy as np
import os
from shutil import rmtree
from unittest.mock import patch, call
import warnings
import sys
from mock import patch, call
from datetime import date
import json

import logging
log = logging.getLogger(__name__)

class TestComputeDataCCL(unittest.TestCase):
    sim_path    = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/New_CCL'
    output_path = sim_path + '/ccl_data/20200101_000000'

    def setUp(self):
        warnings.simplefilter('ignore', category=RuntimeWarning)
        warnings.simplefilter('ignore', category=ResourceWarning)
        
    def tearDown(self):
        if os.path.isdir(self.output_path):
            rmtree(self.output_path)

    @patch('CoLoRe_analysis.compute_data_CCL.datetime')
    @patch('builtins.print')
    def test_normal_output_data(self, mocked_print, mocked_time):
        with open(self.sim_path+ '/all_data.pkl','rb') as input:
            target_values = pickle.load(input) 
            
        np.random.seed(1)
        mocked_time.today.return_value = date(2020,1,1)
        mocked_time.side_effect = lambda *args, **kw: date(*args, **kw)
        compute_data(self.sim_path, zbins=[0,0.15,1])

        # values = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_md_d', 'cl_md_t', 'cl_mm_d', 'cl_mm_t']
        values = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_mm_d', 'cl_mm_t']


        for i, value in enumerate(values):
            np.testing.assert_equal(target_values[i], np.loadtxt(self.output_path + f'/{value}.dat'),f'Mismatching value: { value }')

        with open(self.output_path + '/INFO.json') as json_file:
            data = json.load(json_file)
            self.assertEqual( data['zbins'], [0,0.15,1])
            self.assertEqual( data['id'], '20200101_000000')

    