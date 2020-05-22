import lib.correlations as corrlib
from lib.time_analysis_LSST import Sim0404
import unittest
import os
from shutil import rmtree

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
        

    def test_correlation_tiny_bin(self):
        cs = self.corr_sims

        corr = cs.correlation_in_bin(minz=1,maxz=1.05)

        first_sim_path = cs.sims['300'][0].location

        # Check data was computed
        self.assertTrue( os.path.isdir(first_sim_path + '/data_treated/binned/100_105/source_1'))
        self.assertTrue( os.path.isfile(first_sim_path + '/data_treated/binned/100_105/source_1/mp_e1.dat'))

        # Once we have pais 1 to 1. We can compute the correlation and coeff for each of them

        # There should be a method to output the mean of the correlation and the mean of the coeff.
        self.fail('Finish the test!')
if __name__ == '__main__':
    unittest.main()