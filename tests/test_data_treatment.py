import unittest
import os, sys
from shutil import rmtree
sys.path.append('./')
import lib.data_treatment
from lib.data_treatment import data_treatment
import numpy as np
import glob

@unittest.skipUnless(__name__ == '__main__', 'Only tested if called directly')
class TestDataTreatment(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.getcwd() + '/tests/test_sims/0404'

    def tearDown(self):
        data_treated_path = self.sim_path + '/data_treated'
        if os.path.isdir(data_treated_path):
            rmtree(data_treated_path)
    
    def test_data_treatment_without_bins(self):
        data_treatment(self.sim_path, source=1)

        a = np.loadtxt(self.sim_path + f'/data_treated/source_1/mp_E.dat')

        self.assertEqual(np.mean(a), -8.687597839307397e-09)
        self.assertEqual(a[0], 3.161026775081331630e-04)

    def test_data_treatment_with_bins(self):
        data_treatment(self.sim_path, source=1, minz=0, maxz=200, output_path = self.sim_path + f'/data_treated/source_1')

        a = np.mean(np.loadtxt(self.sim_path + f'/data_treated/source_1/mp_E.dat'))
        self.assertEqual(a, -8.687597839307397e-09)

    def test_data_treatment_with_bins_2(self):
        data_treatment(self.sim_path, source=1, minz=2, maxz=2.01, output_path = self.sim_path + f'/data_treated/source_1')

        a = np.loadtxt(self.sim_path + f'/data_treated/source_1/mp_E.dat')

        self.assertEqual(a[0], 0.00031610267750813316)

if __name__ == '__main__':
    unittest.main()
