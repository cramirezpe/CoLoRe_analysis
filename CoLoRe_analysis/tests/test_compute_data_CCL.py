import unittest
import pickle
import numpy as np
import os
from shutil import rmtree
from unittest.mock import patch, call
import warnings
import sys
from mock import patch, call
from datetime import date
import json
from unittest import skipUnless
from types import SimpleNamespace
from CoLoRe_analysis.tests.test_ccl_reader import mock_compute_data
from CoLoRe_analysis.sims_reader import Sim0404
import CoLoRe_analysis

import logging
log = logging.getLogger(__name__)


@skipUnless('RUN_CCL_TESTS' in os.environ, 'Only run when activated in environment')
class TestComputeDataCCL(unittest.TestCase):
    sim_path    = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/sims/New_CCL'
    analysis_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/New_CCL'
    output_path = analysis_path + '/ccl_data/20200101_000000'

    def setUp(self):
        warnings.simplefilter('ignore', category=RuntimeWarning)
        warnings.simplefilter('ignore', category=ResourceWarning)
        
    def tearDown(self):
        if os.path.isdir(self.analysis_path + '/ccl_data'):
            rmtree(self.analysis_path + '/ccl_data')

    @patch('CoLoRe_analysis.compute_data_CCL.datetime')
    @patch('builtins.print')
    def test_normal_output_data_anafast(self, mocked_print, mocked_time):
        with open(self.analysis_path+ '/all_data_anafast.pkl','rb') as input:
            target_values = pickle.load(input) 
            
        np.random.seed(1)
        mocked_time.today.return_value = date(2020,1,1)
        mocked_time.side_effect = lambda *args, **kw: date(*args, **kw)
        CoLoRe_analysis.compute_data_CCL.compute_data(self.sim_path, self.analysis_path, zbins=[0,0.15,1],code='anafast')

        # values = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_md_d', 'cl_md_t', 'cl_mm_d', 'cl_mm_t']
        values = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_mm_d', 'cl_mm_t']


        for i, value in enumerate(values):
            np.testing.assert_equal(target_values[i], np.loadtxt(self.output_path + f'/{value}.dat'),f'Mismatching value: { value }')

        with open(self.output_path + '/INFO.json') as json_file:
            data = json.load(json_file)
            self.assertEqual( data['zbins'], [0,0.15,1])
            self.assertEqual( data['id'], '20200101_000000')
            self.assertEqual( data['code'], 'anafast')
    
    @patch('CoLoRe_analysis.compute_data_CCL.datetime')
    @patch('builtins.print')
    def test_normal_output_data_namaster(self, mocked_print, mocked_time):
        with open(self.analysis_path+ '/all_data_namaster.pkl','rb') as input:
            target_values = pickle.load(input) 

        np.random.seed(1)
        mocked_time.today.return_value = date(2020,1,1)
        mocked_time.side_effect = lambda *args, **kw: date(*args, **kw)
        CoLoRe_analysis.compute_data_CCL.compute_data(self.sim_path, self.analysis_path, zbins=[0, 0.15, 1], code='namaster')

        names = ['pairs', 'shotnoise', 'nz_tot', 'z_nz', 'cl_dd_d', 'cl_dd_t', 'cl_dm_d', 'cl_dm_t', 'cl_mm_d', 'cl_mm_t']

        for i, value in enumerate(names):
            np.testing.assert_almost_equal(target_values[i], np.loadtxt(self.output_path + f'/{value}.dat'),err_msg=f'Mismatching value: { value }')

        with open(self.output_path + '/INFO.json') as json_file:
            data = json.load(json_file)
            self.assertEqual( data['zbins'], [0, 0.15, 1] )
            self.assertEqual( data['id'], '20200101_000000')
            self.assertEqual( data['code'], 'namaster')

class TestMainFunction(unittest.TestCase):
    empty_output = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/empty_ccl'
    new_output   = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/test_output'
    wrong_output = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/New'
    exist_output = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/New_CCL'
    sim_location = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/sims/New_CCL'

    args = SimpleNamespace(
        input=sim_location, 
        output=None,
        param=None,
        source=3,
        nside=128,
        max_files=None,
        downsampling=1,
        zbins=[0,0.15,1],
        nz_h=50,
        nz_min=0,
        nz_max=None,
        code='anafast'
    )

    def setUp(self):
        try:
            os.makedirs(self.empty_output)
        except FileExistsError:
            rmtree( self.empty_output )
            os.makedirs( self.empty_output )

    def tearDown(self):
        if os.path.isdir( self.empty_output ):
            rmtree( self.empty_output )

        if os.path.isdir( self.new_output ):
            rmtree( self.new_output )

        ccl_data_dir =  self.exist_output + '/ccl_data'
        if os.path.isdir( ccl_data_dir ):
            rmtree( ccl_data_dir )

    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    def test_output_exists_and_empty(self, mock_func):
        self.args.input = self.sim_location
        self.args.output= self.empty_output
        self.args.param = self.sim_location + '/param.cfg'

        with self.assertRaises(FileNotFoundError):
            CoLoRe_analysis.compute_data_CCL.main(self.args)

        assert not mock_func.called

    @patch('CoLoRe_analysis.ccl_reader.compute_data')
    def test_raise_when_no_paramcfg(self, mock_func):
        self.args.input     = self.sim_location
        self.args.output    = self.wrong_output
        self.args.param     = self.sim_location + '/no_param.cfg'

        with self.assertRaises(FileNotFoundError):
            CoLoRe_analysis.compute_data_CCL.main(self.args)

        assert not mock_func.called
        
    @patch('CoLoRe_analysis.ccl_reader.compute_data')
    def test_output_exists_with_wrong_sim(self, mock_func):
        self.args.input     = self.sim_location
        self.args.output    = self.wrong_output
        self.args.param     = self.sim_location + '/param.cfg'

        with self.assertRaises(ValueError):
            CoLoRe_analysis.compute_data_CCL.main(self.args)

        assert not mock_func.called

    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    @patch('builtins.print')
    def test_output_exists_with_correct_info(self, mock_print, mock_func):
        self.args.input     = self.sim_location
        self.args.output    = self.exist_output
        self.args.param     = self.sim_location + '/param.cfg'
        self.args.source    = 3

        CoLoRe_analysis.compute_data_CCL.main(self.args)

        cl_mm_t = np.loadtxt(self.args.output + '/ccl_data/20200101_000000/cl_mm_t.dat')
        np.testing.assert_equal(cl_mm_t, [1,2,3])

        sim = Sim0404(self.exist_output)
        sim.set_ccl_reader()
        output = sim.ccl_reader.search_output()
        self.assertEqual(output[0]['source'], 3)

    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    @patch('builtins.print')
    def test_output_does_not_exist(self, mock_print, mock_func):
        self.args.input     = self.sim_location
        self.args.output    = self.new_output
        self.args.param     = self.sim_location + '/param.cfg'
        self.args.source     = 3

        CoLoRe_analysis.compute_data_CCL.main(self.args)

        cl_mm_t = np.loadtxt(self.args.output + '/ccl_data/20200101_000000/cl_mm_t.dat')
        np.testing.assert_equal(cl_mm_t, [1,2,3])

        sim = Sim0404(self.args.output)
        sim.set_ccl_reader()
        output = sim.ccl_reader.search_output()
        self.assertEqual(output[0]['source'], 3)


