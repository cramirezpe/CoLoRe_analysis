import unittest
import os, sys
from shutil import rmtree
sys.path.append('./')
import CoLoRe_analysis.compute_data_shear
from CoLoRe_analysis.compute_data_shear import data_treatment
import numpy as np
import glob

class TestDataTreatment(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/0404'

    def tearDown(self):
        data_treated_path = self.sim_path + '/data_treated'
        if os.path.isdir(data_treated_path):
            rmtree(data_treated_path)
    
    def test_data_treatment_without_bins(self):
        data_treatment(self.sim_path, source=2,do_cls=True,do_kappa=True)

        a = np.loadtxt(self.sim_path + f'/data_treated/source_2/mp_E.dat')
        b = np.loadtxt(self.sim_path + f'/data_treated/source_2/cld_dd.dat')
        d = np.loadtxt(self.sim_path + f'/data_treated/source_2/cld_kk.dat')
    
        self.assertEqual(np.mean(a), 1.3593664904906463e-11)
        self.assertEqual(a[0]      , 1.0001937620402216e-05)
        self.assertEqual(np.mean(b), 0.00530553916038216)
        self.assertEqual(np.mean(d), 3.2987881842564064e-11)
        

    def test_data_treatment_with_bins_2(self):
        # This will be saved as 200,201 in a regular basis. Just for testing pourpuses. In real usage It won't work well for this precision level
        data_treatment(self.sim_path, source=2, minz=2, maxz=2.005, output_path = self.sim_path + f'/data_treated/binned/200_2005/source_2', do_cls=False, do_kappa=False)

        a = np.loadtxt(self.sim_path + f'/data_treated/binned/200_2005/source_2/mp_E.dat')

        self.assertEqual(np.mean(a), -4.153934804547951e-11)

if __name__ == '__main__':
    unittest.main()