from lib.file_manager import FileManager, FilterList
import unittest
import os

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.filters = FilterList.filters()

    def test_get_simulations(self):
        filt = self.filters[3][1]
        result = FileManager.get_simulations(os.getcwd() + '/tests/test_sims',param_filter=filt)
        self.assertIn( os.getcwd() + '/tests/test_sims/0404', result )