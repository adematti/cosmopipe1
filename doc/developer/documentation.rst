.. _developer-documentation:

Documentation
=============

Please follow `Sphinx style guide`_ when writing the documentation (except for file names) and `PEP257`_ for docstrings.

Building
--------

The documentation can be built in or outside the Docker image::

  cd $HOME/cosmopipe/doc
  make html

Changes to the ``rst`` files can be made from outside the Docker container.
You can display the website (outside the Docker container) by opening ``_build/html/index.html/``.

Finally, to push the documentation, `Read the Docs`_.


References
----------

.. target-notes::

.. _`Sphinx style guide`: https://documentation-style-guide-sphinx.readthedocs.io/en/latest/style-guide.html

.. _`PEP257`: https://www.python.org/dev/peps/pep-0257/

.. _`Read the Docs`: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/read-the-docs.html
