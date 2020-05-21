import lib.shear_reader as module
import unittest
import os
from lib.shear_reader import ShearReader
from mock import patch
from shutil import rmtree

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
        


if __name__ == '__main__':
    unittest.main()