import lib.shear_reader as module
import unittest
import os
from lib.shear_reader import ShearReader
from mock import patch, call
from shutil import rmtree
import numpy as np
import sys
from lib.data_treatment import savetofile
from lib.data_treatment import data_treatment

def mock_data_treatment(path,source=1, do_cls=False, do_kappa=False, minz=None,maxz=None, output_path=None):
    if not output_path:
        output_path = path + f'/data_treated/source_{ source }'
    os.makedirs(output_path, exist_ok=True)

    minz = 0 if minz==None else minz
    maxz = 2000 if maxz==None else maxz

    mp_e1 = [1,2,3]
    mp_E  = [21,22,23]
    savetofile(output_path, [mp_e1,mp_E],['mp_e1','mp_E'])
    if do_cls:
        cld_dd = [4,5,6]
        savetofile(output_path, [cld_dd],['cld_dd'])
    
    if do_kappa:
        mp_k   = [7,8,9]
        if do_cls:
            cld_kk = [10,11,12]
            savetofile(output_path, [cld_kk],['cld_kk'])
        savetofile(output_path, [mp_k],["mp_k"])

class TestShearReader(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.getcwd() + '/tests/test_sims/0404'
        self.sr = ShearReader( self.sim_path )

    def tearDown(self):
        data_treated_path = self.sim_path + '/data_treated'
        if os.path.isdir(data_treated_path):
            rmtree(self.sim_path + '/data_treated')
    
    @patch('lib.shear_reader.data_treatment',side_effect=mock_data_treatment)
    def test_creation_when_does_not_exist(self, mock_func):
        a = self.sr.get_values('mp_E', source=1, compute=True)
        self.assertTrue( os.path.isfile(self.sim_path + '/data_treated/source_1/mp_E.dat') )
        self.assertEqual(a[0], 21)

    @patch.object(ShearReader, "do_data_treatment")
    def test_not_created_when_exists(self, mock_func):
        path = self.sim_path + '/data_treated/source_2'
        os.makedirs( path )
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=2)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)
        
    @patch('lib.shear_reader.data_treatment',side_effect=mock_data_treatment)
    def test_creation_when_does_not_exist_binned(self, mock_func):
        a = self.sr.get_values('mp_E', source=1, minz=1, maxz=2.10, compute=True)
        expected_file = self.sim_path + '/data_treated/binned/100_210/source_1/mp_E.dat'
        
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0], 21)

    def test_raise_when_does_not_exist_and_no_compute(self):
        self.sr.remove_data_treated()

        with self.assertRaises(OSError):
            a = self.sr.get_values('mp_E', source=1, minz=1, maxz=2.10)


    @patch.object(ShearReader, "do_data_treatment")
    def test_not_created_when_exists_binned(self, mock_func):
        path = self.sim_path + '/data_treated/binned/300_301/source_3'
        os.makedirs(path)
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=3, minz=3, maxz=3.01)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)

    @patch('lib.shear_reader.data_treatment',side_effect=mock_data_treatment)
    def test_binned_statistics(self, mock_func):
        self.sr.compute_binned_statistics(1,1.1,2)

        path_head   = self.sim_path + f'/data_treated/binned/'
        path_tail    = '/source_1/mp_E.dat'

        vals = self.sr.get_values('mp_e1',source=1,minz=1,maxz=1.05)
        for str in '100_105','105_110':
            self.assertEqual( vals[0], 1)
            self.assertTrue( os.path.isfile(path_head + str + path_tail), path_head+str+path_tail)


    def test_removed_data_treated(self):
        path = self.sim_path + '/data_treated/zz/zz'
        os.makedirs(path)
        self.sr.remove_data_treated()
        self.assertFalse( os.path.isdir(path) )

if __name__ == '__main__':
    unittest.main()