.. ESGF Pyclient documentation master file, created by
   sphinx-quickstart on Sat Oct 20 10:37:44 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to esgf-pyclient  documentation!
========================================

ESGF Pyclient is a Python package designed for interacting with the `Earth System Grid Federation`_ system.  Current development is focussed on support for the ESGF Search API.

ESGF Pyclient is currently in development and should be considered alpha-quality software.  Anyone wishing to contribute or give feedback can do so through the project's `github site`_

Getting Started
===============

The package can be downloaded via ``pip`` or ``easy_install``::

  $ pip install esgf-pyclient
  $ easy_install esgf-pyclient

The source code is available on github at https://github.com/stephenpascoe/esgf-pyclient

Once installed you import the package as the name ``pyesgf``.  See the recipes for examples.


Contents
========

.. toctree::
   :maxdepth: 2

   concepts
   examples
   search_api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _`Earth System Grid Federation`: http://esgf.org
.. _`github site`: https://github.com/stephenpascoe/esgf-pyclient
