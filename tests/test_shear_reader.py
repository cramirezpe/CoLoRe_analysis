import lib.shear_reader as module
import unittest
import os
from lib.shear_reader import ShearReader
from mock import patch
from shutil import rmtree
import numpy as np

class TestShearReader(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.getcwd() + '/tests/test_sims/0404'
        self.sr = ShearReader( self.sim_path )

    def tearDown(self):
        data_treated_path = self.sim_path + '/data_treated'
        if os.path.isdir(data_treated_path):
            rmtree(self.sim_path + '/data_treated')
    
    def test_creation_when_does_not_exist(self):
        a = self.sr.get_values('mp_E', source=1)
        self.assertTrue( os.path.isfile(self.sim_path + '/data_treated/source_1/mp_E.dat'), self.sim_path + '/data_treatment/source_1/mp_E.dat')

        self.assertEqual(a[0], 0.00031610267750813316)

    @patch.object(ShearReader, "do_data_treatment")
    def test_not_created_when_exists(self, mock_func):
        path = self.sim_path + '/data_treated/source_2'
        os.makedirs( path )
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=2)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)
        
    def test_creation_when_does_not_exist_binned(self):
        a = self.sr.get_values('mp_E', source=1, minz=2, maxz=2.01)
        expected_file = self.sim_path + '/data_treated/binned/200_201/source_1/mp_E.dat'
        
        self.assertTrue( os.path.isfile(expected_file) )
        a = np.loadtxt(expected_file)
        self.assertEqual(a[0], 0.00031610267750813316)

    @patch.object(ShearReader, "do_data_treatment")
    def test_not_created_when_exists_binned(self, mock_func):
        path = self.sim_path + '/data_treated/binned/300_301/source_3'
        os.makedirs(path)
        with open( path + '/mp_e1.dat', 'a') as the_file:
            the_file.write('3141592653\n')
        vals = self.sr.get_values('mp_e1', source=3, minz=3, maxz=3.01)
        mock_func.assert_not_called()
        self.assertEqual(vals,3141592653)

    def test_binned_statistics(self):
        self.sr.compute_binned_statistics(1,2,4)

        path_head   = self.sim_path + f'/data_treated/binned/'
        path_tail    = '/source_1/mp_E.dat'

        for str in '100_125','125_150','150_175','175_200':
            self.assertTrue( os.path.isfile(path_head + str + path_tail), path_head+str+path_tail)

if __name__ == '__main__':
    unittest.main()