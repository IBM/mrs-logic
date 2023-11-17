from .. import util
from ..context import Context, Options
from .converter import Converter

__all__ = [
    'ConverterULKB',
]

Context._default_options.to_ulkb = Options({
    'annotate_ep_lnk': False,
    'annotate_ep_properties': False,
    'annotate_sense_labels': False,
    'annotate_senses': False,
    'bind_evars': True,
    'bind_ivars': True,
    'bind_uvars': True,
    'drop_evars': False,
    'drop_ivars': False,
    'drop_uvars': False,
    'mk_p_equal': [],
    'mk_q_exists': [],
    'mk_q_exists1': [],
    'mk_q_forall': [],
    'mk_q_forall': [],
    'passthrough': [],
    'translate_predicates': True,
    'translate_quantifiers': True,
    'universe_type': None,
})


class ConverterULKB(Converter, format='ulkb'):

    _var_prefixes = {'x', 'e', 'i', 'u'}
    _p2ulkb_map = {}
    _p2ulkb = {
        '_mk_p_equal': {        # CARG = ARG0
            'named',
        },
        '_mk_p_implies': {      # ARG1 -> ARG2   (ARG0 is ignored)
            '_if_x_then',
        },
        '_mk_p_not': {
            'neg',
        }
    }
    _q2ulkb_map = {}
    _q2ulkb = {
        '_mk_q_exists': {       # (∃x, RSTR ∧ BODY)
            '_a_q',
            '_another_q',
            '_any_q',
            '_both_q',
            '_each_q',
            '_some_q',
            '_some_q_indiv',
            '_that_q_dem',
            '_this_q_dem',
            '_which_q',
            'free_relative_q',
            'def_explicit_q',
            'def_implicit_q',
            'idiom_q_i',
            'number_q',
            'pronoun_q',
            'proper_q',
            'udef_q',
        },
        '_mk_q_exists1': {      # (∃!x, RSTR ∧ BODY)
            '_the_q',
            'which_q',
        },
        '_mk_q_forall': {       # (∀x, RSTR -> BODY)
            '_all_q',
            '_every_q',
            'every_q',
        },
        '_mk_q_forall_implies_not': {  # (∀x, RSTR → ¬BODY)
            '_no_q',
        }
    }

    def _optseq(self, opt):
        v = self._opt.get(opt, [])
        if not isinstance(v, (list, tuple, set)):
            v = [v]
        self._opt[opt] = set(v)

    def __init__(self, solution, context=None, **kwargs):
        import ulkb
        super().__init__(solution, **kwargs)
        # options
        self._opt = Options({**self._context.options.to_ulkb, **kwargs})
        self._optseq('mk_p_equal')
        self._optseq('mk_p_not')
        self._optseq('mk_q_exists')
        self._optseq('mk_q_exists1')
        self._optseq('mk_q_forall')
        self._optseq('mk_q_forall_implies_not')
        self._optseq('passthrough')
        # initialization
        self._ulkb = ulkb
        if self._opt.universe_type is None:
            self._aty = map(
                lambda i: self._ulkb.TypeVariable(f'a{i}'), util.count(0))
        else:
            self._aty = util.repeat(self._opt.universe_type)
        self._ex_bound_var_prefixes = set()
        self._var_prefixes = self.__class__._var_prefixes.copy()
        if self._opt.bind_evars:
            self._ex_bound_var_prefixes.add('e')
        if self._opt.bind_ivars:
            self._ex_bound_var_prefixes.add('i')
        if self._opt.bind_uvars:
            self._ex_bound_var_prefixes.add('u')
        if self._opt.drop_evars:
            self._var_prefixes.remove('e')
        if self._opt.drop_ivars:
            self._var_prefixes.remove('i')
        if self._opt.drop_uvars:
            self._var_prefixes.remove('u')
        # Setup predicate translation table.
        if self._opt.mk_p_equal or self._opt.mk_p_not:
            self._p2ulkb_map = self.__class__._p2ulkb_map.copy()
            for p in self._opt.mk_p_equal:
                self._p2ulkb_map[p] = self.__class__._mk_p_equal
            for p in self._opt.mk_p_not:
                self._p2ulkb_map[p] = self.__class__._mk_p_not
        # Setup quantifier translation table.
        if (self._mk_q_exists
            or self._opt.mk_q_exists1
            or self._opt.mk_q_forall
                or self._mk_q_forall_implies_not):
            self._q2ulkb_map = self.__class__._q2ulkb_map.copy()
            for mk in {'_mk_q_exists', '_mk_q_exists1', '_mk_q_forall',
                       '_mk_q_forall_implies_not'}:
                for q in self._opt[mk[1:]]:
                    self._q2ulkb_map[q] = getattr(self.__class__, mk)
        self._scopes = self._solution.scopes
        self._root = self._solution.root
        self._plugs = self._solution.plugs
        self._estack = []       # evar stack

    def _do_convert(self):
        if self._opt.annotate_senses:
            self._senses = self._solution.solver.senses
        else:
            self._senses = {}
        self._cons = {}                            # carg cache
        self._vars = self._do_convert_variables()  # arg cache
        form = self._ep_to_ulkb(*self._scopes[self._root])
        vars = util.peekable(filter(
            lambda v: v.id[0] in self._ex_bound_var_prefixes,
            sorted(form.get_free_variables())))
        if vars:
            form = self._ulkb.Exists(*vars, form)
        return form

    def _do_convert_variables(self):
        return {
            id: self._ulkb.Variable(id, next(self._aty), **(
                kwargs if self._opt.annotate_ep_properties else {}))
            for id, kwargs in self._solution.mrs.variables.items()
            if id[0] in self._var_prefixes
        }

    def _ep_to_ulkb(self, ep, *args):
        eps = util.chain([ep], args)
        if self._context._logger.isEnabledFor(util.logging.DEBUG):
            eps = list(eps)
            self._context._logger.debug('%s', str(eps))
        if args:
            return self._estack_flush(self._ulkb.And(*map(self._ep_to_ulkb, eps)))
        if ep.is_quantifier():
            var = self._vars[ep.iv]
            rstr = self._estack_flush(self._ep_to_ulkb(
                *self._get_scopes_plugs(ep.args['RSTR'])))
            body = self._estack_flush(self._ep_to_ulkb(
                *self._get_scopes_plugs(ep.args['BODY'])))
            return self._mk_q(ep, var, rstr, body)
        else:
            return self._mk_p(ep, *map(self._ep_arg_to_ulkb,
                                       self._get_ep_args_iterator(ep)))

    def _ep_arg_to_ulkb(self, arg):
        if arg.startswith('h'):  # higher-order
            return self._ep_to_ulkb(*self._get_scopes_plugs(arg))
        else:                   # 1st-order
            return self._vars[arg]

    def _get_scopes_plugs(self, h):
        return self._scopes[self._plugs.get(h, h)]

    def _get_ep_args_iterator(self, ep):
        for k in map(lambda i: f'ARG{i}', util.count(0)):
            if k not in ep.args:
                break
            prefix = ep.args[k][0]
            if prefix != 'h' and prefix not in self._var_prefixes:
                continue
            yield ep.args[k]

    def _estack_push(self, evar):
        self._estack.append(evar)

    def _estack_flush(self, form):
        if not self._opt.bind_evars:
            return form         # nothing to do
        while self._estack:
            form = self._ulkb.Exists(self._estack.pop(), form)
        return form

    def _mk_p(self, ep, *args):
        kwargs = {}
        if self._opt.annotate_ep_lnk:
            kwargs['lnk'] = ep.lnk
        if ep.id in self._senses:
            sense_id, sense_label = self._senses[ep.id]
            kwargs['sense'] = sense_id
            if self._opt.annotate_sense_labels:
                kwargs['label'] = f'{sense_label}.{sense_id}'
        if ep.carg is not None:
            if ep.carg not in self._cons:
                self._cons[ep.carg] = self._ulkb.Constant(
                    ep.carg, next(self._aty))
            args = [self._cons[ep.carg], *args]
        if (self._opt.translate_predicates
            and ep.predicate not in self._opt.passthrough
                and ep.predicate in self._p2ulkb_map):
            return self._p2ulkb_map[ep.predicate](
                self, *args).with_annotations(**kwargs)
        else:
            if len(args) == 0:
                tp = self._ulkb.BoolType()
            else:
                if (self._opt.bind_evars  # predicate introduces evar
                    and args[0].is_variable()
                        and args[0].id[0] == 'e'):
                    self._estack_push(args[0])
                tp = self._ulkb.FunctionType(
                    *util.take(len(args), self._aty),
                    self._ulkb.BoolType())
            p = self._ulkb.Constant(ep.predicate, tp, **kwargs)
            return p(*args)

    def _mk_p_equal(self, *args):
        args = util.take(2, filter(
            lambda x: x.is_constant() or (
                x.is_variable() and x.id[0] == 'x'), args))
        return self._ulkb.Equal(*args)

    def _mk_p_implies(self, *args):  # FIXME: too ad-hoc?
        assert len(args) > 1
        rhs, lhs = args[-2], args[-1]
        if rhs.is_application():
            op, *args = rhs.unfold_application()
            if op.id == '_then_a_1' and len(args) > 0:
                rhs = args[-1]
        return self._ulkb.Implies(lhs, rhs)

    def _mk_p_not(self, *args):  # FIXME: too ad-hoc?
        args = util.take(1, filter(
            lambda x: x.type.is_bool_type(), args))
        return self._ulkb.Not(self._estack_flush(*args))

    def _mk_q(self, ep, var, rstr, body):
        if (self._opt.translate_quantifiers
            and ep.predicate not in self._opt.passthrough
                and ep.predicate in self._q2ulkb_map):
            return self._q2ulkb_map[ep.predicate](self, var, rstr, body)
        else:
            p = self._ulkb.Constant(
                ep.predicate,
                self._ulkb.FunctionType(var.type, self._ulkb.BoolType()))
            return p(self._ulkb.Abstraction(var, self._ulkb.And(rstr, body)))

    def _mk_q_exists(self, x, rstr, body):
        return self._ulkb.Exists(x, self._ulkb.And(rstr, body))

    def _mk_q_exists1(self, x, rstr, body):
        return self._ulkb.Exists1(x, self._ulkb.And(rstr, body))

    def _mk_q_forall(self, x, rstr, body):
        return self._ulkb.Forall(x, self._ulkb.Implies(rstr, body))

    def _mk_q_forall_implies_not(self, x, rstr, body):
        return self._ulkb.Forall(
            x, self._ulkb.Implies(rstr, self._ulkb.Not(body)))


_p2ulkb_map = ConverterULKB._p2ulkb_map
for name, ps in ConverterULKB._p2ulkb.items():
    method = getattr(ConverterULKB, name)
    for p in ps:
        if p in _p2ulkb_map:
            raise RuntimeError(f'duplicated predicate in _p2ulkb: {p}')
        _p2ulkb_map[p] = method

_q2ulkb_map = ConverterULKB._q2ulkb_map
for name, qs in ConverterULKB._q2ulkb.items():
    method = getattr(ConverterULKB, name)
    for q in qs:
        if q in _q2ulkb_map:
            raise RuntimeError(f'duplicated quantifier in _q2ulkb: {q}')
        _q2ulkb_map[q] = method
