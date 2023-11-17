import unittest

from ulkb import *

from mrs_logic import solve
from mrs_logic.solution import Solution

settings.serializer.ulkb.show_types = False
settings.serializer.ulkb.show_annotations = False

aty = TypeVariable('a')
Brown = Constant('Brown', aty)
_be_v_id = Constant('_be_v_id', FunctionType(aty, aty, aty, bool))
_brown_a_1 = Constant('_brown_a_1', FunctionType(aty, aty, bool))
_dog_n_1 = Constant('_dog_n_1', FunctionType(aty, bool))


class TestSolution(unittest.TestCase):

    def test_opt_annotate_senses(self):
        # success: annotate_senses=True
        sn = next(solve('Some dogs are brown.'))
        form = sn.to_ulkb(
            universe_type=aty, annotate_senses=True, senses_as_labels=True)
        _, t = form.unfold_exists()
        l, _ = t.unfold_and()
        self.assertTrue(l.equal(
            (_dog_n_1.with_annotations(sense='02084071-n'))
            (Variable('x3', aty)), deep=True))

        # success: annotate_senses=False
        form = sn.to_ulkb(universe_type=aty, annotate_senses=False)
        _, t = form.unfold_exists()
        l, _ = t.unfold_and()
        self.assertTrue(l.equal(
            (_dog_n_1.with_annotations())
            (Variable('x3', aty)), deep=True))

    def test_opt_bind_evars(self):
        # success: bind_evars=True (default)
        sn = next(solve('Some dogs are brown.'))
        form = sn.to_ulkb(universe_type=aty, bind_evars=True)
        e, x = Variables('e', 'x', aty)
        self.assertEqual(
            form,
            Exists(x, And(_dog_n_1(x), Exists(e, _brown_a_1(e, x)))))

        # success: bind_evars=False
        sn = next(solve('Some dogs are brown.'))
        form = sn.to_ulkb(universe_type=aty, bind_evars=False)
        e, x = Variables('e2', 'x3', aty)
        self.assertEqual(
            form,
            Exists(x, And(_dog_n_1(x), _brown_a_1(e, x))))

    def test_opt_mk_q_exists(self):
        sn = next(solve('The dog is brown.'))
        form = sn.to_ulkb(
            universe_type=aty, mk_q_exists='_the_q', bind_evars=True)
        e, x, y = Variables('e', 'x', 'y', aty)
        self.assertEqual(
            form,
            Exists(x, Equal(Brown, x)
                   & Exists(y, _dog_n_1(y) & Exists(e, _be_v_id(e, y, x)))))

    def test_opt_universe_type(self):
        # success: universe_type=None
        sn = next(solve('Some dogs are brown.'))
        form = sn.to_ulkb()
        x, body = form.unfold_exists()
        left, right = body.unfold_and()
        self.assertEqual(
            left,
            Constant('_dog_n_1', FunctionType(x.type, bool))(x))
        e, _ = right.unfold_exists()
        self.assertEqual(
            right,
            Exists(e, Constant(
                '_brown_a_1',
                FunctionType(e.type, x.type, bool))(e, x)))


if __name__ == '__main__':
    unittest.main()
