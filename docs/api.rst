Reference
=========

.. currentmodule:: mrs_logic

API functions
-------------

.. autosummary::
   :toctree: generated/

   get_current_context
   parse
   solve
   solve1

Context
-------

Context-management:

.. autosummary::
   :toctree: generated/

   Context
   Context.options
   Context.ace
   Context.ukb
   Context.reset_ace
   Context.reset_ukb

Solver
------

Solver object:

.. autosummary::
   :toctree: generated/

   Solver
   Solver.context
   Solver.mrs
   Solver.scopes
   Solver.senses
   Solver.is_solvable
   Solver.count_solutions
   Solver.iterate_solutions
   SolverError

Solution
--------

Solution object:

.. autosummary::
   :toctree: generated/

   Solution
   Solution.solver
   Solution.context
   Solution.mrs
   Solution.scopes
   Solution.senses
   Solution.index
   Solution.root
   Solution.plugs
   Solution.entails
   Solution.to_dot
   Solution.to_prolog
   Solution.to_pydot
   Solution.to_ulkb
   Solution.to_z3
