Configuration
=============

Examples of configuration files are given in the `setup` folder.

Setting up the acquisition board
--------------------------------

Currently, only National instruments boards are implemented, based on NI-DAQmx (`nidaqmx` package).
Create a board object as follows:

.. code:: Python

    from clampy import *
    board = NI()

