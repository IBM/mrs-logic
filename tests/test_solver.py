import unittest

from mrs_logic import Context, Solver, SolverError, parse
from mrs_logic.solution import Solution


class TestSolver(unittest.TestCase):

    _mrs = next(parse('Every cat likes some dog.'))
    _solver = Solver(_mrs)

    def test_context(self):
        self.assertEqual(
            TestSolver._solver.context, Context.get_current_context())

    def test_mrs(self):
        self.assertEqual(
            TestSolver._solver.mrs, TestSolver._mrs)

    def test_scopes(self):
        scopes = TestSolver._solver.scopes
        self.assertEqual(
            set(scopes.keys()), {'h4', 'h7', 'h1', 'h9', 'h12'})

    def test_senses(self):
        senses = TestSolver._solver.senses
        self.assertEqual(senses, {
            'x3': ('02121620-n', 'cat'),
            'e2': ('01777210-v', 'like'),
            'x8': ('02084071-n', 'dog')})

    def test_is_solvable(self):
        self.assertTrue(TestSolver._solver.is_solvable())

    def test_count_solutions(self):
        self.assertEqual(TestSolver._solver.count_solutions(), 2)
        solver = Solver(next(parse('The sky is blue.')))
        self.assertEqual(solver.count_solutions(), 1)

    def test_iterate_solutions(self):
        # success
        sols = list(TestSolver._solver.iterate_solutions())
        self.assertEqual(len(sols), 2)
        self.assertIsInstance(sols[0], Solution)
        self.assertIsInstance(sols[1], Solution)

        # success: start=1
        sols1 = list(TestSolver._solver.iterate_solutions(start=1))
        self.assertEqual(len(sols1), 1)
        self.assertEqual(sols[1].root, sols1[0].root)
        self.assertDictEqual(sols[1].plugs, sols1[0].plugs)

        # success: stop=1
        sols0 = list(TestSolver._solver.iterate_solutions(stop=1))
        self.assertEqual(len(sols0), 1)
        self.assertEqual(sols[0].root, sols0[0].root)
        self.assertDictEqual(sols[0].plugs, sols0[0].plugs)


if __name__ == '__main__':
    unittest.main()
