import CoLoRe_analysis.ccl_reader as ccl_reader
from CoLoRe_analysis.compute_data_shear import savetofile
import unittest
from mock import patch, call
from shutil import rmtree
import os
import numpy as np

from CoLoRe_analysis.ccl_reader import CCLReader
import CoLoRe_analysis.compute_data_CCL

from CoLoRe_analysis.debug_tools import debug_on

def mock_compute_data(path, source=1, output_path=None):
    if not output_path:
        output_path = path + f'/ccl_data/source_{ source }/'
        
    os.makedirs(output_path, exist_ok=True)

    cl_mm_t = [1,2,3]
    pairs   = [(0,0), (0,1), (1,1)]
    nz_tot  = [4,5,6]

    savetofile(output_path, [cl_mm_t,pairs,nz_tot],['cl_mm_t','pairs','nz_tot'])


class TestCCLReader(unittest.TestCase):
    def setUp(self):
        self.sim_path    = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/New_CCL'
        self.cr     =  CCLReader( self.sim_path )
        self.computed_data_path = self.sim_path + '/ccl_data'

    def tearDown(self):
        if os.path.isdir(self.computed_data_path):
            rmtree(self.computed_data_path)

    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    def test_do_data_computations(self, mock_func):
        self.cr.do_data_computations( source=1 )
        cl_mm_t = np.loadtxt(self.computed_data_path + '/source_1/cl_mm_t.dat')
        np.testing.assert_equal(cl_mm_t, [1,2,3])

    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    def test_creation_when_does_not_exist(self, mock_func):
        nz_tot = self.cr.get_values('nz_tot', compute=True)
        np.testing.assert_equal(nz_tot, [4,5,6])

    @patch('CoLoRe_analysis.ccl_reader.compute_data')
    def test_obtain_when_does_exist_without_computing(self, mock_func):
        path = self.computed_data_path + '/source_2'
        os.makedirs(path)
        with open(path + '/pairs.dat','a') as f:
            f.write('231\n')
        vals = self.cr.get_values('pairs', source=2)
        mock_func.assert_not_called()
        np.testing.assert_equal(vals, 231)

    def test_raise_when_compute_false_and_dont_exist(self):
        with self.assertRaises(OSError):
            a = self.cr.get_values('pairs')


    def test_remove_computed_data(self): 
        path = self.computed_data_path + '/zz/zz'
        os.makedirs(path)
        self.cr.remove_computed_data()
        self.assertFalse( os.path.isdir(path) )

