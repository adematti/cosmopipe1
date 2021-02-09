.. _developer-docker:

Building the Docker image
=========================

First create an account ``youraccount`` at `<https://hub.docker.com>`_.

To build, go into the root directory and run::

  docker-compose build

Or, alternatively::

   docker build -f docker/Dockerfile -t cosmopipe .

To tag and push::

  docker tag cosmopipe youraccount/cosmopipe:tag
  docker login
  docker push youraccount/cosmopipe:tag
