import unittest

from delphin.codecs import mrsprolog
from delphin.mrs._mrs import MRS

from mrs_logic import Solver, get_current_context, parse, solve
from mrs_logic.ace import ACE
from mrs_logic.ukb import UKB


class TestMRSLogic(unittest.TestCase):

    def test_parse(self):
        ctx = get_current_context()

        # success: input is ACE response
        ret = list(parse(ctx.ace.parse('The sky is blue.')))
        self.assertEqual(len(ret), 2)
        self.assertIsInstance(ret[0], MRS)
        self.assertIsInstance(ret[1], MRS)

        # success: input is str
        ret = list(parse('The sky is blue.'))
        self.assertEqual(len(ret), 2)
        self.assertIsInstance(ret[0], MRS)
        self.assertIsInstance(ret[1], MRS)
        saved_ret = ret

        # success: start=1
        ret = list(parse('The sky is blue.', start=1))
        self.assertEqual(len(ret), 1)
        self.assertEqual(
            mrsprolog.encode(ret[0]),
            mrsprolog.encode(saved_ret[1]))

        # success: stop=1
        ret = list(parse('The sky is blue.', stop=1))
        self.assertEqual(len(ret), 1)
        self.assertEqual(
            mrsprolog.encode(ret[0]),
            mrsprolog.encode(saved_ret[0]))

        # success: step=2
        ret = list(parse('Every man loves a woman.'))
        self.assertEqual(len(ret), 6)
        saved_ret = ret
        ret = list(parse('Every man loves a woman.', step=2))
        self.assertEqual(len(ret), 3)
        self.assertEqual(
            mrsprolog.encode(ret[0]),
            mrsprolog.encode(saved_ret[0]))
        self.assertEqual(
            mrsprolog.encode(ret[1]),
            mrsprolog.encode(saved_ret[2]))
        self.assertEqual(
            mrsprolog.encode(ret[2]),
            mrsprolog.encode(saved_ret[4]))

        # success: input=mrs
        ctx = get_current_context()
        ret = list(parse(ctx.ace.parse('The sky is blue.')))
        self.assertEqual(len(ret), 2)
        self.assertIsInstance(ret[0], MRS)
        self.assertIsInstance(ret[1], MRS)

    def test_solve(self):
        from ulkb import (And, Constant, Exists, Exists1, FunctionType,
                          TypeVariable, Variable, Variables)

        ret = list(solve('The sky is blue.'))
        self.assertEqual(len(ret), 3)

        aty = TypeVariable('a')
        x3, x8, i13, e2 = Variables('x3', 'x8', 'i13', 'e2', aty)

        _sky_n_1 = Constant('_sky_n_1', FunctionType(aty, bool))
        _blue_a_1 = Constant('_blue_a_1', FunctionType(aty, aty, bool))
        _be_v_id = Constant('_be_v_id', FunctionType(aty, aty, aty, bool))

        A = ret[0].to_ulkb(universe_type=aty)
        self.assertEqual(
            A,
            Exists1(x3, And(_sky_n_1(x3), Exists(e2, _blue_a_1(e2, x3)))))

        B = ret[1].to_ulkb(universe_type=aty)
        self.assertEqual(
            B,
            Exists(i13, x8, And(
                _blue_a_1(x8, i13),
                Exists1(x3, And(_sky_n_1(x3), Exists(
                    e2, _be_v_id(e2, x3, x8)))))))

        C = ret[2].to_ulkb(universe_type=aty)
        self.assertEqual(
            C,
            Exists(i13,
                   Exists1(x3, And(
                       _sky_n_1(x3),
                       Exists(x8, And(
                           _blue_a_1(x8, i13),
                           Exists(e2, _be_v_id(e2, x3, x8))))))))

        # success: input is str
        ret = list(solve('Every man loves a woman.'))
        self.assertEqual(len(ret), 21)

        # success: input is MRS iterator
        ret = list(solve(parse('Every man loves a woman.')))
        self.assertEqual(len(ret), 21)

        # success: input is single MRS
        mrs = next(parse('Every man loves a woman', start=3))
        self.assertEqual(
            len(list(solve(mrs))),
            Solver(mrs).count_solutions())

        # success: order='dfs' vs order='bfs'
        dfs = list(map(
            lambda s: s.index,
            solve('Every man loves a woman.', order='dfs')))
        bfs = list(map(
            lambda s: s.index,
            solve('Every man loves a woman.', order='bfs')))
        self.assertNotEqual(dfs, bfs)
        self.assertEqual(len(dfs), len(bfs))
        self.assertEqual(sorted(dfs), bfs)


if __name__ == '__main__':
    unittest.main()
