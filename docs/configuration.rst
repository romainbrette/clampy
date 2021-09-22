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

An input channel is specified by giving a name to a physical channel, with a gain:

.. code:: Python

    from clampy.setup.units import *
    board.set_analog_input('output1', channel=0, gain=10*mV/nA)