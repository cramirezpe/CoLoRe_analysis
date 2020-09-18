import os
import unittest

from CoLoRe_analysis.file_manager import FileManager, FilterList


class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.filters = FilterList.filters()

    def test_get_simulations(self):
        filt = self.filters[3][1]
        result = FileManager.get_simulations(os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis',param_filter=filt)
        self.assertIn( os.path.dirname(os.path.realpath(__file__)) + '/test_sims/analysis/0404', result )
