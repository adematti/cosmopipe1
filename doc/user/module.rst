.. _user-module:

Modules
=======

**cosmopipe** is structured in **modules** (e.g. a theory model). As in CosmoSIS, they should include the following routines:

  - ``setup``: run once, when the pipeline is set up
  - ``execute``: run during sampling
  - ``cleanup``: run at exit, to free variables

So far **cosmopipe** only accepts Python modules. These can either inherit from ``BaseModule``:

.. code-block:: python

  class MyModule(BaseModule):

    # Attributes: config_block (holds config parameters) and data_block (holds all data used in the run)

    def setup(self):
        # setup module (called at the beginning)

    def execute(self):
        # execute, i.e. do calculation (called at each step)

    def cleanup(self):
        # cleanup, i.e. free variables if needed (called at the end)

Or have the three functions in a file:

.. code-block:: python

  def setup(config_block, data_block):
      # setup module (called at the beginning)

  def execute(config_block, data_block):
      # execute, i.e. do calculation (called at each step)

  def cleanup(config_block, data_block):
      # cleanup, i.e. free variables if needed (called at the end)


Code structure
==============

A ``BasePipeline`` inherits from ``BaseModule`` and can setup, execute and cleanup several modules.
A ``BaseLikelihood`` is a ``BasePipeline`` that computes ``loglkl`` based on some data and model.

In diagrammatic representation (``BaseModule.plot_inheritance_graph(graph_fn)``):

  .. image:: ../static/inheritance.png
