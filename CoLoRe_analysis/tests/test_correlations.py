import os
import unittest
from shutil import rmtree

import numpy as np
from mock import patch

from CoLoRe_analysis import correlations, shear_reader, sims_reader

class TestCorrelations(unittest.TestCase):
    def setUp(self):
        # Prepare the sim objects
        self.location    = os.path.dirname(os.path.realpath(__file__))
        self.simNew      = sims_reader.Sim0404(self.location + '/test_sims/analysis/New', "New")
        self.simNew_rep  = sims_reader.Sim0404(self.location + '/test_sims/analysis/New', "Newrep")
        self.simNew_s2   = sims_reader.Sim0404(self.location + '/test_sims/analysis/New_s2', "New_s2")
        self.simOld      = sims_reader.Sim0404(self.location + '/test_sims/analysis/Old', "Old")
        self.simOld_wrong= sims_reader.Sim0404(self.location + '/test_sims/analysis/Old_false_seed',    "Old_wrong")  
        self.simOld_s2   = sims_reader.Sim0404(self.location + '/test_sims/analysis/Old_s2', 'Old_s2')

        # Prepare corrleations object
        self.corr_sims   = correlations.CorrelateTwoShears([self.simNew, self.simNew_rep, self.simNew_s2],[self.simOld,self.simOld_wrong, self.simOld_s2])
        self.all_names    = [i[x].__name__ for x in range(2) for i in self.corr_sims.sims.values()]

    def tearDown(self):
        sims = (self.simNew, self.simNew_rep, self.simNew_s2, self.simOld, self.simOld_wrong, self.simOld_s2)
        for sim in sims:
            if os.path.isdir(sim.analysis_location + '/shear_data'):
                rmtree(sim.analysis_location + '/shear_data')

    def prepare_mock_data(self):
        path_a = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/Old/shear_data/binned/100_105/source_1'
        path_b = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/Old_s2/shear_data/binned/100_105/source_1'
        path_c = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/New/shear_data/binned/100_105/source_1'
        path_d = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/New_s2/shear_data/binned/100_105/source_1'
        
        for path in path_a,path_b,path_c,path_d:
            os.makedirs(path)
            open(path + '/mp_e2.dat','a').close()

        np.savetxt(path_a + '/mp_e2.dat', [1,3,4,5])
        np.savetxt(path_b + '/mp_e2.dat', [1,3,4,4])
        np.savetxt(path_c + '/mp_e2.dat', [1,9,4,5])
        np.savetxt(path_d + '/mp_e2.dat', [1,2,2,2])

    def test_input(self):
        with self.assertRaises(ValueError):
            _ = correlations.CorrelateTwoShears(self.simNew, [self.simOld, self.simOld_wrong])
        with self.assertRaises(ValueError):
            _ = correlations.CorrelateTwoShears((self.simNew), "he")

    def test_repeated_seed_is_eliminated(self):
        self.assertFalse( 'Newrep' in self.all_names and 'New' in self.all_names, f'Newrep and New in sims: { self.all_names }')

    def test_unmatched_seed_is_eliminated(self):
        self.assertNotIn('Old_false_seed', self.all_names)

    def test_matched_seeds(self):
        # The matched seeds are 300 and 1003
        self.assertSetEqual( self.corr_sims.seeds, {1003,300} )

        # Program should match simulations run with the same seed. 
        self.assertEqual( ['New_s2', 'Old_s2'] , [x.__name__ for x in self.corr_sims.sims[300]])
    
    @patch.object(shear_reader.ShearReader, "do_compute_data_shear")
    def test_correlation_regression_tiny_bin(self, mock_func):
        self.prepare_mock_data()
        cs = self.corr_sims
        corr = cs.correlation_in_bin(parameter='mp_e2', minz=1, maxz=1.05)

        first_sim_path = cs.sims[300][0].analysis_location

        # Check data was computed
        self.assertTrue( os.path.isdir(first_sim_path + '/shear_data/binned/100_105/source_1'))
        self.assertFalse( os.path.isfile(first_sim_path + '/shear_data/binned/100_105/source_1/mp_e1.dat'))


        self.assertEqual( corr, 0.6855447840406176)

        coef, intercept = cs.regression_in_bin(parameter='mp_e2', minz=1, maxz=1.05)
        self.assertAlmostEqual( intercept, 0.2659033078880413)
        self.assertAlmostEqual( coef, 1.4440203562340965)
        
        mock_func.assert_not_called()

    def test_saved_correlation(self):
        self.prepare_mock_data()

        mult_cs = self.corr_sims
        good_cs = correlations.CorrelateTwoShears([self.simNew],[self.simOld])
        
        # Multiple simulations won't have a defined place to be stored
        with self.assertRaises(ValueError):
            mult_cs.store_correlation(parameter='mp_e2',minz=1,maxz=1.05)
        
        mult_cs.store_correlation(parameter='mp_e2', minz=1, maxz=1.05, out=mult_cs.sims[300][0].analysis_location + '/shear_data')
        x = np.loadtxt(mult_cs.sims[300][0].analysis_location + '/shear_data/mp_e2.dat')

        self.assertAlmostEqual(x, 0.6855447840406176)

        good_cs.store_correlation(parameter='mp_e2', minz=1, maxz=1.05)
        
        self.assertAlmostEqual(good_cs.get_correlation(parameter='mp_e2',minz=1, maxz=1.05), 0.42828052649917187)

    def test_saved_regression(self):
        self.prepare_mock_data()

        mult_cs = self.corr_sims
        good_cs = correlations.CorrelateTwoShears([self.simNew],[self.simOld])
        
        # Multiple simulations won't have a defined place to be stored
        with self.assertRaises(ValueError):
            mult_cs.store_regression(parameter='mp_e2',minz=1,maxz=1.05)
        
        mult_cs.store_regression(parameter='mp_e2',minz=1,maxz=1.05, out= mult_cs.sims[300][0].analysis_location + '/shear_data')
        x = np.loadtxt(mult_cs.sims[300][0].analysis_location + '/shear_data/coef_mp_e2.dat')
        y = np.loadtxt(mult_cs.sims[300][0].analysis_location + '/shear_data/intercept_mp_e2.dat')
        self.assertAlmostEqual(x, 1.4440203562340965)
        self.assertAlmostEqual(y, 0.2659033078880413)

        good_cs.store_regression(parameter='mp_e2', minz=1, maxz=1.05)
        
        self.assertAlmostEqual(good_cs.get_regression(reg_parameter = 'coef', parameter='mp_e2',minz=1, maxz=1.05), 0.22137404580152661)
        self.assertAlmostEqual(good_cs.get_regression(reg_parameter = 'intercept', parameter='mp_e2',minz=1, maxz=1.05), 2.1984732824427486)
    
    def test_path_to_regression(self):
        param     = "mp_e2"
        source    = 2
        self.prepare_mock_data()

        cs = correlations.CorrelateTwoShears([self.simNew],[self.simOld])
        self.assertEqual(cs.path_to_regression(parameter=param, source=source), self.simNew.analysis_location + f'/shear_data/regressions/source_2/{ self.simNew.preparation_time }/')

    def test_get_regression(self):
        with self.assertRaises(ValueError):
           self.corr_sims.get_regression('234')
            
            
    def test_path_to_correlation(self):
        param = 'mp_e2'
        source = 2
        self.prepare_mock_data()
        
        cs = correlations.CorrelateTwoShears([self.simNew],[self.simOld])
        self.assertEqual(cs.path_to_correlation(parameter=param, source=source), self.simNew.analysis_location + f'/shear_data/correlations/source_2/{ self.simNew.preparation_time }/')

if __name__ == '__main__':
    unittest.main()
