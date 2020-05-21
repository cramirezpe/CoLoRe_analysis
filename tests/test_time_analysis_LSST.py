import lib.time_analysis_LSST as module
import unittest
from lib.time_analysis_LSST import (FileManager, MemoryReader, FilterList, Simulation, Sim0404)
import os
import filecmp
from shutil import rmtree

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.filters = FilterList.filters()

    def test_get_simulations(self):
        filt = self.filters[3][1]
        result = FileManager.get_simulations(os.getcwd() + '/tests/test_sims',param_filter=filt)
        self.assertIn( os.getcwd() + '/tests/test_sims/0404', result )

class TestSimulationMaster(unittest.TestCase):
    def setUp(self):
        self.sim_path = os.getcwd() + '/tests/test_sims/0404'
        self.Sim      = Sim0404( self.sim_path, 'testname')
    
    def tearDown(self):
        data_treated_path = self.sim_path + '/data_treated'
        if os.path.isdir(data_treated_path):
            rmtree(self.sim_path + '/data_treated')

    def test_set_simulation(self):
        sim         = self.Sim
        self.assertEqual(sim.__name__, 'testname')
        self.assertEqual(sim.version, 'master')
        self.assertEqual(sim.seed, '1003')
        self.assertEqual(sim.factor, '0.01')
        self.assertEqual(sim.template, 'master_with_shear')
        self.assertEqual(sim.status, 'done')
        self.assertEqual(sim.preparation_time, '20200416090110')

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

        #self.assertEqual( self.Sim.size, '13M')

    def test_shear_reader(self):
        self.Sim.set_shear_reader()
        shear_reader = self.Sim.shear_reader
        shear_reader.do_data_treatment()
        shear_reader.do_data_treatment(source=2)

        with open(self.sim_path+f'/data_treated/source_1/mp_E.dat') as f:
            first_line = f.readline()
        self.assertEqual(first_line, '3.161026775081331630e-04\n')



if __name__ == '__main__':
    unittest.main()