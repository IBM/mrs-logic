import unittest

from mrs_logic import Context, Solver, SolverError, parse
from mrs_logic.solution import Solution


class TestSolution(unittest.TestCase):

    _mrs = next(parse('Every cat likes some dog.'))
    _solver = Solver(_mrs)
    _solutions = list(_solver.iterate_solutions())
    _sol0 = _solutions[0]
    _sol1 = _solutions[1]

    def test_context(self):
        self.assertEqual(
            TestSolution._sol0.context, TestSolution._solver.context)
        self.assertEqual(
            TestSolution._sol1.context, TestSolution._solver.context)

    def test_solver(self):
        self.assertEqual(TestSolution._sol0.solver, TestSolution._solver)
        self.assertEqual(TestSolution._sol1.solver, TestSolution._solver)

    def test_mrs(self):
        self.assertEqual(TestSolution._sol0.mrs, TestSolution._mrs)
        self.assertEqual(TestSolution._sol1.mrs, TestSolution._mrs)

    def test_scopes(self):
        self.assertEqual(
            TestSolution._sol0.scopes, TestSolution._solver.scopes)
        self.assertEqual(
            TestSolution._sol1.scopes, TestSolution._solver.scopes)

    def test_index(self):
        self.assertEqual(TestSolution._sol0.index, 0)
        self.assertEqual(TestSolution._sol1.index, 1)

    def test_root(self):
        self.assertEqual(TestSolution._sol0.root, 'h9')
        self.assertEqual(TestSolution._sol1.root, 'h4')

    def test_plugs(self):
        self.assertDictEqual(TestSolution._sol0.plugs, {
            'h5': 'h7',
            'h6': 'h1',
            'h10': 'h12',
            'h11': 'h4'})
        self.assertDictEqual(TestSolution._sol1.plugs, {
            'h5': 'h7',
            'h6': 'h9',
            'h10': 'h12',
            'h11': 'h1'})

    def test_to_z3(self):
        s0 = TestSolution._sol0.to_z3()
        self.assertEqual(str(s0), '''\
Exists(x8,
       And(_dog_n_1(x8),
           ForAll(x3,
                  Implies(_cat_n_1(x3),
                          Exists(e2, _like_v_1(e2, x3, x8))))))''')

        s1 = TestSolution._sol1.to_z3()
        self.assertEqual(str(s1), '''\
ForAll(x3,
       Implies(_cat_n_1(x3),
               Exists(x8,
                      And(_dog_n_1(x8),
                          Exists(e2, _like_v_1(e2, x3, x8))))))''')

    def test_dot(self):
        s0 = TestSolution._sol0.to_dot()
        self.assertEqual(str(s0), '''\
digraph domgraph {
node [shape=plaintext];
   h4 [label="_every_q"];
node [shape=point, label=""];
   h5;
node [shape=point, label=""];
   h6;
node [shape=plaintext];
   h7 [label="_cat_n_1"];
node [shape=plaintext];
   h1 [label="_like_v_1"];
node [shape=plaintext];
   h9 [label="_some_q_indiv"];
node [shape=point, label=""];
   h10;
node [shape=point, label=""];
   h11;
node [shape=plaintext];
   h12 [label="_dog_n_1"];
   h4 -> h5 [arrowhead=nonenone];
   h4 -> h6 [arrowhead=nonenone];
   h9 -> h10 [arrowhead=nonenone];
   h9 -> h11 [arrowhead=nonenone];
   h10 -> h12 [arrowhead=nonenone, style=dotted];
   h11 -> h4 [arrowhead=nonenone, style=dotted];
   h5 -> h7 [arrowhead=nonenone, style=dotted];
   h6 -> h1 [arrowhead=nonenone, style=dotted];
}
''')
        s1 = TestSolution._sol1.to_dot()
        self.assertEqual(str(s1), '''\
digraph domgraph {
node [shape=plaintext];
   h4 [label="_every_q"];
node [shape=point, label=""];
   h5;
node [shape=point, label=""];
   h6;
node [shape=plaintext];
   h7 [label="_cat_n_1"];
node [shape=plaintext];
   h1 [label="_like_v_1"];
node [shape=plaintext];
   h9 [label="_some_q_indiv"];
node [shape=point, label=""];
   h10;
node [shape=point, label=""];
   h11;
node [shape=plaintext];
   h12 [label="_dog_n_1"];
   h4 -> h5 [arrowhead=nonenone];
   h4 -> h6 [arrowhead=nonenone];
   h9 -> h10 [arrowhead=nonenone];
   h9 -> h11 [arrowhead=nonenone];
   h5 -> h7 [arrowhead=nonenone, style=dotted];
   h6 -> h9 [arrowhead=nonenone, style=dotted];
   h10 -> h12 [arrowhead=nonenone, style=dotted];
   h11 -> h1 [arrowhead=nonenone, style=dotted];
}
''')

    def test_pydot(self):
        from pydot import Dot
        s0 = TestSolution._sol0.to_pydot()
        self.assertIsInstance(s0, Dot)
        s1 = TestSolution._sol1.to_pydot()
        self.assertIsInstance(s1, Dot)

    def test_prolog(self):
        s0 = TestSolution._sol0.to_prolog()
        self.assertEqual(s0, "\
'_some_q_indiv'('_dog_n_1','_every_q'('_cat_n_1','_like_v_1'))")


if __name__ == '__main__':
    unittest.main()
