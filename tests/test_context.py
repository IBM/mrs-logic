import unittest

from mrs_logic import Context
from mrs_logic.ace import ACE
from mrs_logic.ukb import UKB


class TestContext(unittest.TestCase):

    def test_get_current_context(self):
        ctx = Context.get_current_context()
        self.assertIsNotNone(ctx)
        self.assertIsNotNone(ctx.ace)
        self.assertIsNotNone(ctx.ukb)

    def test__enter__(self):
        ctx0 = Context.get_current_context()
        ctx1 = Context()
        with ctx1:
            self.assertIs(Context.get_current_context(), ctx1)
        self.assertIs(Context.get_current_context(), ctx0)

    def test_reset_ace(self):
        ctx = Context.get_current_context()
        old_ace = ctx.ace
        new_ace = ctx.reset_ace()
        self.assertIsInstance(new_ace, ACE)
        self.assertIsNot(new_ace, old_ace)

    def test_reset_ukb(self):
        ctx = Context.get_current_context()
        old_ukb = ctx.ukb
        new_ukb = ctx.reset_ukb()
        self.assertIsInstance(new_ukb, UKB)
        self.assertIsNot(new_ukb, old_ukb)


if __name__ == '__main__':
    unittest.main()
