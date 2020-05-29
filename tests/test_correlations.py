import lib.correlations as corrlib
from lib.time_analysis_LSST import Sim0404
from lib.shear_reader import ShearReader
import unittest
import os
from shutil import rmtree
import numpy as np
from mock import patch

class TestCorrelations(unittest.TestCase):
    def setUp(self):
        # Prepare the sim objects
        self.location    = os.getcwd()
        self.simNew      = Sim0404(self.location + '/tests/test_sims/New', "New")
        self.simNew_rep  = Sim0404(self.location + '/tests/test_sims/New', "Newrep")
        self.simNew_s2   = Sim0404(self.location + '/tests/test_sims/New_s2', "New_s2")
        self.simOld      = Sim0404(self.location + '/tests/test_sims/Old', "Old")
        self.simOld_wrong= Sim0404(self.location + '/tests/test_sims/Old_false_seed',    "Old_wrong")  
        self.simOld_s2   = Sim0404(self.location + '/tests/test_sims/Old_s2', 'Old_s2')

        # Prepare corrleations object
        self.corr_sims   = corrlib.CorrelateTwoShears([self.simNew, self.simNew_rep, self.simNew_s2],[self.simOld,self.simOld_wrong, self.simOld_s2])
        self.all_names    = [i[x].__name__ for x in range(2) for i in self.corr_sims.sims.values()]

    def tearDown(self):
        sims = (self.simNew, self.simNew_rep, self.simNew_s2, self.simOld, self.simOld_wrong, self.simOld_s2)
        for sim in sims:
            if os.path.isdir(sim.location + '/data_treated'):
                rmtree(sim.location + '/data_treated')

    def prepare_mock_data(self):
        path_a = os.getcwd() + '/tests/test_sims/Old/data_treated/binned/100_105/source_1'
        path_b = os.getcwd() + '/tests/test_sims/Old_s2/data_treated/binned/100_105/source_1'
        path_c = os.getcwd() + '/tests/test_sims/New/data_treated/binned/100_105/source_1'
        path_d = os.getcwd() + '/tests/test_sims/New_s2/data_treated/binned/100_105/source_1'
        
        for path in path_a,path_b,path_c,path_d:
            os.makedirs(path)
            open(path + '/mp_e2.dat','a').close()

        np.savetxt(path_a + '/mp_e2.dat', [1,3,4,5])
        np.savetxt(path_b + '/mp_e2.dat', [1,3,4,4])
        np.savetxt(path_c + '/mp_e2.dat', [1,9,4,5])
        np.savetxt(path_d + '/mp_e2.dat', [1,2,2,2])

    def test_input(self):
        with self.assertRaises(ValueError):
            _ = corrlib.CorrelateTwoShears(self.simNew, [self.simOld, self.simOld_wrong])
        with self.assertRaises(ValueError):
            _ = corrlib.CorrelateTwoShears((self.simNew), "he")

    def test_repeated_seed_is_eliminated(self):
        self.assertFalse( 'Newrep' in self.all_names and 'New' in self.all_names, f'Newrep and New in sims: { self.all_names }')

    def test_unmatched_seed_is_eliminated(self):
        self.assertNotIn('Old_false_seed', self.all_names)

    def test_matched_seeds(self):
        # The matched seeds are 300 and 1003
        self.assertSetEqual( self.corr_sims.seeds, {'1003','300'} )

        # Program should match simulations run with the same seed. 
        self.assertEqual( ['New_s2', 'Old_s2'] , [x.__name__ for x in self.corr_sims.sims['300']])
    
    @patch.object(ShearReader, "do_data_treatment")
    def test_correlation_regression_tiny_bin(self, mock_func):
        self.prepare_mock_data()
        cs = self.corr_sims
        corr = cs.correlation_in_bin(parameter='mp_e2',minz=1,maxz=1.05)
        mock_func.assert_not_called()

        first_sim_path = cs.sims['300'][0].location

        # Check data was computed
        self.assertTrue( os.path.isdir(first_sim_path + '/data_treated/binned/100_105/source_1'))
        self.assertFalse( os.path.isfile(first_sim_path + '/data_treated/binned/100_105/source_1/mp_e1.dat'))


        self.assertEqual( corr, 0.6855447840406176)

        coef, intercept = cs.regression_in_bin(parameter='mp_e2', minz=1, maxz=1.05)
        self.assertEqual( intercept, 0.2659033078880413)
        self.assertEqual( coef, 1.4440203562340965)

    def test_saved_correlation(self):
        self.prepare_mock_data()

        mult_cs = self.corr_sims
        good_cs = corrlib.CorrelateTwoShears([self.simNew],[self.simOld])
        
        # Multiple simulations won't have a defined place to be stored
        with self.assertRaises(ValueError):
            mult_cs.store_correlation(parameter='mp_e2',minz=1,maxz=1.05)
        
        mult_cs.store_correlation(parameter='mp_e2',minz=1,maxz=1.05, out= mult_cs.sims['300'][0].location + '/data_treated')
        x = np.loadtxt(mult_cs.sims['300'][0].location + '/data_treated/mp_e2.dat')

        self.assertEqual(x, 0.6855447840406176)

        good_cs.store_correlation(parameter='mp_e2', minz=1, maxz=1.05)
        
        self.assertEqual(good_cs.get_correlation(parameter='mp_e2',minz=1, maxz=1.05), 0.42828052649917187)
    
    def test_path_to_correlation(self):
        param = 'mp_e2'
        source = 2
        self.prepare_mock_data()
        
        cs = corrlib.CorrelateTwoShears([self.simNew],[self.simOld])
        self.assertEqual(cs.path_to_correlation(parameter=param, source=source), self.simNew.location + f'/data_treated/correlations/source_2/{ self.simNew.preparation_time }/')

if __name__ == '__main__':
    unittest.main()