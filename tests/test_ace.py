import unittest

from mrs_logic.ace import ACE, ACE_Error


class TestACE(unittest.TestCase):

    def test__init__(self):
        # failure: bad grammar
        self.assertRaisesRegex(
            ACE_Error, 'no such grammar file', ACE, grammar='-nonexistent-')

        # success: default grammar
        ace = ACE()
        self.assertIsNotNone(ace)
        self.assertIsNotNone(ace._grammar)

    def test_parse(self):
        ret = ACE().parse('The sky is blue.')
        self.assertTrue(len(ret.results()) > 0)


if __name__ == '__main__':
    unittest.main()
