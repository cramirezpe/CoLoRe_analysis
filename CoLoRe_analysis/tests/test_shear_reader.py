import os
import sys
import unittest
from shutil import rmtree

import numpy as np
from mock import call, patch

from CoLoRe_analysis import shear_reader, compute_data_shear, shear_reader

def mock_compute_data_shear(path, source=1, do_cls=False, do_kappa=False, minz=None, maxz=None, output_path=None):
    if not output_path:
        output_path = path + f'/shear_data/source_{ source }'
    os.makedirs(output_path, exist_ok=True)

    minz = 0 if minz==None else minz
    maxz = 2000 if maxz==None else maxz

    mp_e1 = [1,2,3]
    mp_E  = [21,22,23]
    compute_data_shear.savetofile(output_path, [mp_e1,mp_E],['mp_e1','mp_E'])
    if do_cls:
        cld_dd = [4,5,6]
        compute_data_shear.savetofile(output_path, [cld_dd],['cld_dd'])
    
    if do_kappa:
        mp_k   = [7,8,9]
        if do_cls:
            cld_kk = [10,11,12]
            compute_data_shear.savetofile(output_path, [cld_kk],['cld_kk'])
        compute_data_shear.savetofile(output_path, [mp_k],["mp_k"])

class TestShearReader(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/sims/0404'
        self.analysis_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis'
        self.sr = shear_reader.ShearReader( self.sim_path , self.analysis_path)

    def tearDown(self):
        shear_data_path = self.sim_path + '/shear_data'
        if os.path.isdir(shear_data_path):
            rmtree(self.sim_path + '/shear_data')
    
    @patch('CoLoRe_analysis.shear_reader.compute_data_shear',side_effect=mock_compute_data_shear)
    def test_creation_when_does_not_exist(self, mock_func):
        a = self.sr.get_values('mp_E', source=1, compute=True)
        self.assertTrue( os.path.isfile(self.analysis_path + '/shear_data/source_1/mp_E.dat') )
        self.assertEqual(a[0], 21)

    @patch('CoLoRe_analysis.shear_reader.compute_data_shear',side_effect=mock_compute_data_shear)
    def test_get_cls_and_kappa(self, mock_func):
        a = self.sr.get_values('mp_k', source=1, minz=1, maxz=2.10, compute=True)
        expected_file = self.analysis_path + '/shear_data/binned/100_210/source_1/mp_k.dat'
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0],7)
    
        a = self.sr.get_values('cld_dd', source=1, minz=1, maxz=2.10, compute=True, do_kappa=True)
        expected_file = self.analysis_path + '/shear_data/binned/100_210/source_1/cld_dd.dat'
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0],4)
  
        expected_file = self.analysis_path + '/shear_data/binned/100_210/source_1/cld_kk.dat'
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0],10)


    @patch.object(shear_reader.ShearReader, "do_compute_data_shear")
    def test_not_created_when_exists(self, mock_func):
        path = self.analysis_path + '/shear_data/source_2'
        os.makedirs( path )
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=2)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)
        
    @patch('CoLoRe_analysis.shear_reader.compute_data_shear',side_effect=mock_compute_data_shear)
    def test_creation_when_does_not_exist_binned(self, mock_func):
        a = self.sr.get_values('mp_E', source=1, minz=1, maxz=2.10, compute=True)
        expected_file = self.analysis_path + '/shear_data/binned/100_210/source_1/mp_E.dat'
        
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0], 21)

    @patch('builtins.input', return_value='y')
    @patch('builtins.print')
    def test_raise_when_does_not_exist_and_no_compute(self, mocked_print, mocked_input):
        self.sr.remove_shear_data()

        with self.assertRaises(OSError):
            a = self.sr.get_values('mp_E', source=1, minz=1, maxz=2.10)


    @patch.object(shear_reader.ShearReader, "do_compute_data_shear")
    def test_not_created_when_exists_binned(self, mock_func):
        path = self.analysis_path + '/shear_data/binned/300_301/source_3'
        os.makedirs(path)
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=3, minz=3, maxz=3.01)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)

    @patch('CoLoRe_analysis.shear_reader.compute_data_shear',side_effect=mock_compute_data_shear)
    def test_binned_statistics(self, mock_func):
        self.sr.compute_binned_statistics(1,1.1,2)

        path_head   = self.analysis_path + f'/shear_data/binned/'
        path_tail    = '/source_1/mp_E.dat'

        vals = self.sr.get_values('mp_e1',source=1,minz=1,maxz=1.05)
        for str in '100_105','105_110':
            self.assertEqual( vals[0], 1)
            self.assertTrue( os.path.isfile(path_head + str + path_tail), path_head+str+path_tail)

    @patch('builtins.input', return_value='y')
    @patch('builtins.print')
    def test_removed_shear_data(self, mocked_print, mocked_input):
        path = self.analysis_path + '/shear_data/zz/zz'
        os.makedirs(path)
        self.sr.remove_shear_data()
        self.assertFalse( os.path.isdir(path) )

if __name__ == '__main__':
    unittest.main()
