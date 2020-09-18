import unittest

from CoLoRe_analysis import functions

class TestFunctions(unittest.TestCase):
    def test_iterable(self):
        self.assertTrue( functions.check_iterable([1]) )
        self.assertTrue( functions.check_iterable((1,2)))
        self.assertFalse( functions.check_iterable("hola"))

if __name__ == '__main__':
    unittest.main()
