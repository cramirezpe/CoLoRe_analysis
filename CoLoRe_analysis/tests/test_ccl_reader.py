import CoLoRe_analysis.ccl_reader as ccl_reader
from CoLoRe_analysis.compute_data_shear import savetofile
import unittest
from mock import patch, call
from shutil import rmtree
import os
import numpy as np
import json

from CoLoRe_analysis.ccl_reader import CCLReader
import CoLoRe_analysis.compute_data_CCL

from CoLoRe_analysis.debug_tools import debug_on

def mock_compute_data(path,source=1, output_path=None, nside=128, max_files=None, downsampling=1, zbins=[0,0.15,1], nz_h = 50, nz_min=None, nz_max=None):
    if not output_path:
        output_path = path + f'/ccl_data/20200101_000000/'
        
    os.makedirs(output_path, exist_ok=True)

    cl_mm_t = [1,2,3]
    pairs   = [(0,0), (0,1), (1,1)]
    nz_tot  = [4,5,6]

    savetofile(output_path, [cl_mm_t,pairs,nz_tot],['cl_mm_t','pairs','nz_tot'])

    info = {
        'id'            : '20200101_000000',
        'source'        : source,
        'nside'         : nside,
        'max_files'     : max_files,
        'downsampling'  : downsampling,
        'zbins'         : zbins,
        'nz_h'          : nz_h,
        'nz_min'        : nz_min,
        'nz_max'        : nz_max
    }

    with open(output_path + '/INFO.json','w') as outfile:
        json.dump(info, outfile)



class TestCCLReader(unittest.TestCase):
    def setUp(self):
        self.sim_path    = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/New_CCL'
        self.cr     =  CCLReader( self.sim_path )
        self.computed_data_path = self.sim_path + '/ccl_data'

        os.makedirs(self.computed_data_path + '/1')
        os.makedirs(self.computed_data_path + '/4')

        self.data1 = {
            'id'            : '1',
            'source'        : 1,
            'nside'         : 16,
            'max_files'     : None,
            'downsampling'  : 1,
            'zbins'         : [1,2,3],
            'nz_h'          : 100,
            'nz_min'        : 0,
            'nz_max'        : 1100
        }

        self.data4 = {
            'id'            : '4',
            'source'        : 31,
            'nside'         : 16,
            'max_files'     : None,
            'downsampling'  : 17,
            'zbins'         : [10,2,3],
            'nz_h'          : 10011,
            'nz_min'        : 8,
            'nz_max'        : 1100
        }

        self.data_mixed = {
            'nside'     : 16,
            'nz_max'    : 1100,
            'max_files' : None
        }

        self.data_false = {
            'nside' : None
        }
        with open(self.computed_data_path + '/1/INFO.json','w') as outfile:
            json.dump(self.data1, outfile)

        with open(self.computed_data_path + '/4/INFO.json','w') as outfile:
            json.dump(self.data4, outfile)

    def tearDown(self):
        if os.path.isdir(self.computed_data_path):
            rmtree(self.computed_data_path)

    def test_search_ccl_output(self):
        self.assertEqual( self.cr.search_output(**self.data1), [self.data1])
        self.assertEqual( self.cr.search_output(**self.data_mixed), [self.data1,self.data4])
        self.assertEqual( self.cr.search_output(**self.data_false), []  )
        
    def test_no_raises_when_no_info(self):
        os.makedirs(self.computed_data_path + '/8')
        self.assertEqual( self.cr.search_output(**self.data1), [self.data1]) 


    def test_search_with_nothing_to_search(self):
        if os.path.isdir(self.computed_data_path):
            rmtree(self.computed_data_path)
        self.assertEqual( self.cr.search_output(**self.data1), [] )
    
    def test_search_without_results(self):
        for dir_ in os.scandir(self.computed_data_path):
            rmtree(dir_)
        self.assertEqual( self.cr.search_output(**self.data1), [] )
        
    
    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    def test_do_data_computations(self, mock_func):
        self.cr.do_data_computations( source=1 )
        cl_mm_t = np.loadtxt(self.computed_data_path + '/20200101_000000/cl_mm_t.dat')
        np.testing.assert_equal(cl_mm_t, [1,2,3])


    @patch('CoLoRe_analysis.ccl_reader.compute_data', side_effect=mock_compute_data)
    def test_creation_when_does_not_exist(self, mock_func):
        nz_tot = self.cr.get_values('nz_tot', compute=True, nside=128)
        nz_tot = self.cr.get_values('nz_tot', compute=True, nside=128)
        np.testing.assert_equal(nz_tot, [4,5,6])

    @patch('CoLoRe_analysis.ccl_reader.compute_data')
    def test_obtain_when_does_exist_without_computing(self, mock_func):
        path = self.computed_data_path + '/1'
        with open(path + '/pairs.dat','a') as f:
            f.write('231\n')
        vals = self.cr.get_values('pairs', **self.data1)
        mock_func.assert_not_called()
        np.testing.assert_equal(vals, 231)

    @patch('builtins.print')
    def test_yield_multiple_info_when_multple_sims_match(self, mocked_print):
        vals = self.cr.get_values('pairs', **self.data_mixed)
        self.assertEqual( vals, [self.data1, self.data4])

    def test_raise_when_compute_false_and_dont_exist(self):
        with self.assertRaises(FileNotFoundError):
            a = self.cr.get_values('pairs', nz_max=666)


    def test_remove_computed_data(self): 
        path = self.computed_data_path + '/zz/zz'
        os.makedirs(path)
        self.cr.remove_computed_data()
        self.assertFalse( os.path.isdir(path) )

