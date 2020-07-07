import CoLoRe_analysis.functions as f
import unittest

class TestFunctions(unittest.TestCase):
    def test_iterable(self):
        self.assertTrue( f.check_iterable([1]) )
        self.assertTrue( f.check_iterable((1,2)))
        self.assertFalse( f.check_iterable("hola"))

if __name__ == '__main__':
    unittest.main()