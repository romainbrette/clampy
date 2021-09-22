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
    board.set_analog_input('output1', channel=0, gain=100*mV/nA)

The gain is specified as voltage at the board divided by the corresponding measured quantity.
In the example above, a 1 nA signal appears as 100 mV at the board.
The module `clampy.setup.units` defines the ISI values of a few common units. For example, `mV`
is `0.001`.

