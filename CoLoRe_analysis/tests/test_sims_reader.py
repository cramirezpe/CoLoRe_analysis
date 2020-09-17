import CoLoRe_analysis.sims_reader as module
import unittest
from CoLoRe_analysis.file_manager import (FileManager) 
from CoLoRe_analysis.sims_reader import  (MemoryReader, Simulation, Sim0404)
import os
import filecmp
from shutil import rmtree
from mock import patch, call

class TestSimulationMaster(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/sims/0404'
        self.sim_analysis_path = os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/0404'
        self.Sim      = Sim0404( self.sim_analysis_path, 'testname')
    
    def tearDown(self):
        self.data_treated_path = self.sim_analysis_path + '/data_treated'
        if os.path.isdir(self.data_treated_path):
            rmtree(self.data_treated_path)

        if os.path.isfile('out_temp.txt'):
            os.remove('out_temp.txt')

    def test_raw_hours(self):
        self.Sim.set_time_reader()
        
        nodes   = self.Sim.nodes
        ms      = self.Sim.time_reader.times['Total']

        hours   = ms/(1000*60*60)
        raw_hours = hours*nodes

        self.assertEqual(self.Sim.time_reader.raw_hours,raw_hours) 
        
    def test_assert_wrong_version(self):
        with self.assertRaises(TypeError):
            self.Sim.version = 'wrong_version'

    def test_set_simulation(self):
        sim         = self.Sim
        self.assertEqual(sim.__name__, 'testname')
        self.assertEqual(sim.version, 'master')
        self.assertEqual(sim.seed, 1003)
        self.assertEqual(sim.factor, 0.01)
        self.assertEqual(sim.template, 'master_with_shear')
        self.assertEqual(sim.status, 'done')
        self.assertEqual(sim.preparation_time, '20200416090110')

    @patch('builtins.print') #suppress print statements
    def test_get_time_from_string(self, mock_func):
        self.assertEqual(module.get_time_from_string(None),0)
        self.assertEqual(module.get_time_from_string('hola'),0)
        with self.assertRaises(ValueError):
            module.get_time_from_string('3 ms and 4 ms')

    @patch('builtins.print')
    def test_search_string_in_file(self, mock_func):
        file_path = 'out_temp.txt'
        with open(file_path, 'w') as f:
            f.write("Firstline\nsecondline\nthirdline\netc")
        
        self.assertEqual(module.search_1st_string_in_file(file_path, 'ñ23ñlkjqrñkwle'), (None,None))

        os.remove(file_path)

    def test_replace_file(self):
        file_path = 'out_temp.txt'
        with open(file_path, 'w') as f:
            f.write("Firstline\nsecondline\nthirdline\netc")
        
        module.replace_in_file('thirdline','thisislinethree',file_path)
        self.assertEqual(module.search_1st_string_in_file(file_path, 'thisis'), (3,'thisislinethree\n'))

        os.remove(file_path)

    def test_reading_time(self):
        self.Sim.set_time_reader()
        time_reader     = self.Sim.time_reader

        time_reader.get_times()

        times = {
            'Creating Fourier-space density and Newtonian potential': 17627.8, 
            'Transforming density and Newtonian potential': 195774.9, 
            'Normalizing density and Newtonian potential': 1169.9, 
            'Creating physical matter density': 7019.1, 
            'Computing normalization of density field': 6350.1, 
            'Getting point sources 0-th galaxy population': 89606.2, 
            'Getting point sources 1-th galaxy population': 86779.9, 
            'Re-distributing sources across nodes': 303.6, 
            'Getting LOS information': 289004.2, 
            'Writing source catalogs 0-th': 64.5, 
            'Writing source catalogs 1-th': 553.9, 
            'Writing kappa source maps': 12423.3, 
            'Total': 724263.3
        }
        self.assertEqual(time_reader.times, times)

    def test_reading_memory(self):
        self.Sim.set_memory_reader()

        tasks = {0: {'Memory': 77398.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 1: {'Memory': 77398.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 2: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 3: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 4: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 5: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 6: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 7: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 8: {'Memory': 77396.0, 'Gaussian Memory': 77100.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 9: {'Memory': 76646.0, 'Gaussian Memory': 76350.0, 'srcs Memory': 259.0, 'kappa Memory': 0}, 'Total': {'Memory': 773214.0, 'Gaussian Memory': 770250.0, 'srcs Memory': 2590.0, 'kappa Memory': 0}}

        self.assertEqual(self.Sim.memory_reader.tasks, tasks)
        self.assertEqual(self.Sim.nodes, 10)

    def test_size(self):
        self.Sim.set_size()

        self.assertEqual( self.Sim.size, '13M')






if __name__ == '__main__':
    unittest.main()