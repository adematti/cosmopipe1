.. title:: cosmopipe docs

*************************************
Welcome to cosmopipe's documentation!
*************************************

.. toctree::
  :maxdepth: 1
  :caption: User documentation

  user/building
  user/module
  user/example
  api/api

.. toctree::
  :maxdepth: 1
  :caption: Developer documentation

  developer/docker
  developer/documentation
  developer/tests
  developer/contributing
  developer/changes

.. toctree::
  :hidden:

************
Introduction
************

**cosmopipe** is an attempt to design shared DESI pipeline(s) to extract cosmological constraints from clustering data.
This is **not** a cosmological inference code, such a `Cobaya`_, `MontePython`_, `CosmoMC`_ at al., but a (hopefully lightweight) framework
to script analysis pipelines.


What for?
=========

As we are entering the era of precision cosmology with spectroscopic surveys, it becomes mandatory to provide an *easy* way for our collaborators
to reproduce our analyses, from (at least) the clustering catalogs down to the cosmological constraints.
Our collaborators should not have to fork our codes (e.g. theory models) from all over github; these codes should be linked in one place...
and run with the correct versions.
This would be possible by running the codes inside the safe, controlled environment of a `Docker`_ container.

Our collaborators should not have to worry about having the correct parameter files for each code, nor how to connect the output of one code
to the input of another. Ideally, they should only have to deal with **one** (provided) parameter file and **one** output,
and should not need to know anything about cosmology in general.
This would be possible by linking ourselves all codes together, through a **pipeline**.

This **pipeline** could be made flexible enough to cover the clustering analyses of the collaboration. For this, we should not have **one** pipeline,
but a framework to **script** pipelines. For example, once I have the codes (hereafter :ref:`user-module`) to model 2 and 3-pt correlation functions
(as well as their covariance), it should be straightforward for me to run a join 2 and 3-pt analyses, without coding anything else.

Eventually, it should be made **very** easy to code and include new modules, without the need for a global view of the pipeline.
This would be possible by providing a simple module architecture to copy and fill, with either Python, C, C++ or Fortran code.

This is all very similar to `CosmoSIS`_ used by the DES collaboration. DESI deserves such a framework as well!

Quick start-up
==============

For a quick start-up, see :ref:`user-example`.

Acknowledgements
================

No acknowledgements to be made yet!

Changelog
=========

* :doc:`developer/changes`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

References
==========

.. target-notes::

.. _`Cobaya`: https://github.com/CobayaSampler/cobaya

.. _`MontePython`: https://github.com/baudren/montepython_public

.. _`CosmoMC`: https://github.com/cmbant/CosmoMC

.. _`Docker`: https://www.docker.com/

.. _`CosmoSIS`: https://bitbucket.org/joezuntz/cosmosis/src/master
