.. _user-building:

Building
========

**cosmopipe** has many dependencies since it links all codes used by the collaboration.
So there are two methods for installing everything, Docker and from scratch.

cosmopipe with Docker
---------------------

Docker is the preferred method, as **cosmopipe** can be run from a laptop and NERSC using the same Docker image.
The Docker image is available on :dockerroot:`Docker Hub <>`.

On your laptop
^^^^^^^^^^^^^^

First pull::

  docker pull {dockerimage}

To run on-the-fly::

  docker run {dockerimage} ./yourscript.sh

Or in interactive mode, you can bind mount your working directory ``absolutepath``::

  docker run --volume absolutepath:/homedir/ -it {dockerimage} /bin/bash

which allows you to work as usual (type ``exit`` to exit).

On NERSC
^^^^^^^^

First pull::

  shifterimg -v pull {dockerimage}

To run on-the-fly::

  shifter --module=mpich-cle6 --image={dockerimage} ./yourscript.sh

In interactive mode::

  shifter --volume absolutepath:/homedir/ --image={dockerimage} /bin/bash

.. note::

  For further information on shifter, see `shifter docs`_.

cosmopipe from scratch
----------------------

In construction!

References
----------

.. target-notes::

.. _`shifter docs`: https://shifter.readthedocs.io/
