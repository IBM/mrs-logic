import unittest

from mrs_logic import parse
from mrs_logic.ukb import UKB, UKB_Error


class TestUKB(unittest.TestCase):

    def test__init__(self):
        ukb = UKB()
        self.assertIsNotNone(ukb)

    def test_resolve(self):
        mrs = next(parse('The sky is blue.'))
        ukb = UKB()
        ret = ukb.resolve(mrs)
        self.assertDictEqual(ret, {
            'x3': ('09436708-n', 'sky'),
            'e2': ('00370869-a', 'blue')})


if __name__ == '__main__':
    unittest.main()
