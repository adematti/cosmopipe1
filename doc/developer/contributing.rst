.. _developer-contributing:

Contributing
============

Contributions to **cosmopipe** are more than welcome!
Please follow these guidelines before filing a pull request:

* Please abide by `PEP8`_ as much as possible in your code writing, add docstrings and tests for each new functionality.

* Check your changes did not add too many code issues. Run `prospector`_ in :root:`Root directory`. This will be run by `Codacy`_ after pushing to GitHub.

* Check Docker image compiles; see :ref:`developer-docker`.

* Check documentation compiles, with the expected result; see :ref:`developer-documentation`.

* Check all tests pass within the new Docker image; see :ref:`developer-tests`.

* Submit your pull request.

References
----------

.. target-notes::

.. _`prospector`: http://prospector.landscape.io/en/master/

.. _`PEP8`: https://www.python.org/dev/peps/pep-0008/

.. _`Codacy`: https://app.codacy.com/
