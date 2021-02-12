.. _user-framework:

Framework
=========

Modules
-------

**cosmopipe** is structured in **modules** (e.g. a theory model). As in CosmoSIS, they should include the following routines:

  - ``setup``: setup module (called at the beginning)
  - ``execute``: execute, i.e. do calculation (called at each step)
  - ``cleanup``: cleanup, i.e. free variables if needed (called at the end)

So far **cosmopipe** only accepts Python modules. These can either inherit from :class:`~cosmopipe.pipeline.module.BaseModule`:

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

``config_block`` and ``data_block`` inherit (are) from the dictionary-like :class:`~cosmopipe.pipeline.block.DataBlock`,
where elements can be accessed through ``(section,name)``.
When creating new sections, it is good practice to add them to :root:`cosmopipe/pipeline/section_names.py`
and use the Python variable instead, e.g. ``section_names.my_section`` (to avoid typos).

Inheritance diagram
-------------------

A :class:`~cosmopipe.pipeline.module.BasePipeline` inherits from :class:`~cosmopipe.pipeline.module.BaseModule` and can setup, execute and cleanup several modules.
A :class:`~cosmopipe.likelihood.likelihood.BaseLikelihood` is a :class:`~cosmopipe.pipeline.module.BaseModule` that computes ``loglkl`` based on some data and model.

In diagrammatic representation (``BaseModule.plot_inheritance_graph(graph_fn)``):

  .. image:: ../static/inheritance.png

Then, one can script a pipeline linking different **cosmopipe** modules together in a tree structure.
An example of such a script is provided in :ref:`user-scripting`.
