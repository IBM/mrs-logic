============
Introduction
============

Overview
========

MRS Logic is a semantic parsing toolkit, based on ERG and MRS, to convert
text to logic.

ERG is the English Resource Grammar, a broad-coverage computational grammar
of English.

MRS is the Minimal Recursion Semantics, a framework for computational
semantics with support for underspecification.

Quickstart
==========

.. currentmodule:: mrs_logic

We start by loading the MRS Logic library:

.. code-block:: python

   from mrs_logic import *

Function :func:`parse()` parses a sentence into an iterator of MRS objects:

.. code-block:: python

   it = parse('The sky is blue')
