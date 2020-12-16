import glob
import os
import sys
import unittest
from shutil import rmtree
from unittest import skipUnless

import numpy as np

from CoLoRe_analysis import compute_data_shear

@skipUnless('RUN_SHEAR_TESTS' in os.environ, 'Only run when activated in environment')
class TestShearDataComputation(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/sims/0404'
        self.analysis_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/0404'

    def tearDown(self):
        shear_data_path = self.analysis_path + '/shear_data'
        if os.path.isdir(shear_data_path):
            rmtree(shear_data_path)
    
    def test_compute_data_shear_without_bins(self):
        compute_data_shear.compute_data_shear(self.sim_path, source=2, do_cls=True, do_kappa=True, output_path=self.analysis_path + f'/shear_data/source_2')

        a = np.loadtxt(self.analysis_path + f'/shear_data/source_2/mp_E.dat')
        b = np.loadtxt(self.analysis_path + f'/shear_data/source_2/cld_dd.dat')
        d = np.loadtxt(self.analysis_path + f'/shear_data/source_2/cld_kk.dat')
    
        self.assertAlmostEqual(np.mean(a), 1.3593664904906463e-11)
        self.assertAlmostEqual(a[0]      , 1.0001937620402216e-05)
        self.assertAlmostEqual(np.mean(b), 0.00530553916038216)
        self.assertAlmostEqual(np.mean(d), 3.2987881842564064e-11)
        

    def test_compute_data_shear_with_bins_2(self):
        # This will be saved as 200,201 in a regular basis. Just for testing pourpuses. In real usage It won't work well for this precision level
        compute_data_shear.compute_data_shear(self.sim_path, source=2, minz=2, maxz=2.005, output_path = self.analysis_path + f'/shear_data/binned/200_2005/source_2', do_cls=False, do_kappa=False)

        a = np.loadtxt(self.analysis_path + f'/shear_data/binned/200_2005/source_2/mp_E.dat')

        self.assertAlmostEqual(np.mean(a), -4.153934804547951e-11)

if __name__ == '__main__':
    unittest.main()
