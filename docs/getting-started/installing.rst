.. _installing:


.. meta::
    :description lang=en:
        Wavelink Installation - Upto date information on how to properly install and manage Wavelink on various Python
        versions.


Installing
##########


Wavelink 4 currently supports the following `Python <https://www.python.org/downloads/>`_ versions:


+-----------------------------+-------------------------------------------------------+-------------------------------+
| Python Version              | Status                                                | Notes                         |
+=============================+=======================================================+===============================+
| **<= 3.11**                 | .. raw:: html                                         | Versions **3.11** or under    |
|                             |                                                       | are not supported.            |
|                             |   <span class="error-wl">Not Supported</span>         |                               |
|                             |                                                       |                               |
+-----------------------------+-------------------------------------------------------+-------------------------------+
| **3.12, 3.13, 3.14**        | .. raw:: html                                         | These versions have been      |
|                             |                                                       | tested and are supported.     |
|                             |   <span class="success-wl">Fully Supported</span>     |                               |
|                             |                                                       |                               |
+-----------------------------+-------------------------------------------------------+-------------------------------+
| **3.15**                    | .. raw:: html                                         | May require custom index      |
|                             |                                                       |                               |
|                             |   <span class="warn-wl">Check Notes</span>            |                               |
|                             |                                                       |                               |
+-----------------------------+-------------------------------------------------------+-------------------------------+

Commands
========

UV
----------

.. code:: shell

    uv add wavelink


pip
---------

.. code:: shell

    pip install -U wavelink


Extra and Optional Dependencies
===============================

To use certain optional features of Wavelink you will have to install the required packages needed to run them.
The following commands can be used to install Wavelink with optional features:

**For development purposes**:

.. code:: shell

    pip install -U wavelink[dev]


**For documentation purposes**:

.. code:: shell

    pip install -U wavelink[docs]


Custom Index
============

Using Wavelink with ``Python >= 3.15`` may require the use of a custom pip index.
The index allows pip to fetch pre-built wheels for some dependencies that may require build-tools for C/C++ due to not having released their own wheels for recent versions of Python.

Usually with time, dependencies will eventually release wheels for new Python releases.
For convenience we provide an index thanks to `Abstract Umbra <https://github.com/AbstractUmbra>`_


**To install with prebuilt wheels:**

.. code:: shell

    pip install -U wavelink --extra-index-url https://abstractumbra.github.io/pip/


Installation Issues
===================
Make sure you have the latest version of Python installed, or if you prefer, a Python version of **3.12** or greater.
If you have any other issues feel free to search for duplicates and then create a new issue on `GitHub <https://github.com/PythonistaGuild/Wavelink>`_ with as much detail as possible. Including providing the output of pip, your OS details and Python version.