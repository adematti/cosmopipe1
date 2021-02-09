.. _user-example:

Example
=======

Still in construction!
Let's say we want to perform a joint fit of two data vectors ``data1`` and ``data2``, with their own models ``model1`` and ``model2``
and a common covariance matrix ``cov``. Our parameter ``.ini`` file would then be:

.. code-block:: ini

  [main]
  modules = like

  [like]
  module_file = likelihood/likelihood.py
  module_class = JointGaussianLikelihood
  join = like1 like2
  modules = cov

  [like1]
  module_file = likelihood/likelihood.py
  module_class = BaseLikelihood
  modules = data1 model1

  [like2]
  module_file = likelihood/likelihood.py
  module_class = BaseLikelihood
  modules = data2 model2

  [data1]
  module_file = data/data_vector.py
  ;details about how to get the data vector #1

  [model1]
  ;details about model #1

  [data2]
  module_file = data/data_vector.py
  ;details about how to get the data vector #2

  [model2]
  ;details about model #2

  [cov]
  module_file = data/covariance.py
  ;details about how to get the commone covariance


One can achieve the same thing in Python with (for a theory model called ``FlatModel``):

.. code-block:: python

  from cosmopipe.pipeline import BaseModule, BasePipeline, ConfigBlock, SectionBlock
  from cosmopipe.theory import FlatModel
  from cosmopipe.likelihood import BaseLikelihood, JointGaussianLikelihood

  config_block = ConfigBlock(config_fn)
  data1 = BaseModule.from_library(name='data1',options=SectionBlock(config_block,'data1'))
  model1 = FlatModel(name='model1')
  data2 = BaseModule.from_library(name='data2',options=SectionBlock(config_block,'data2'))
  model2 = BaseModule.from_library(name='model2',options=SectionBlock(config_block,'model2'))
  cov = BaseModule.from_library(name='cov',options=SectionBlock(config_block,'cov'))
  like1 = BaseLikelihood(name='like1',modules=[data1,model1])
  like2 = BaseLikelihood(name='like2',modules=[data2,model2])
  like = JointGaussianLikelihood(name='like',join=[like1,like2],modules=[cov])
  pipeline = BasePipeline(modules=[like])

In diagrammatic representation (``pipeline.plot_pipeline_graph(graph_fn)``):

  .. image:: ../static/pipe3.png
