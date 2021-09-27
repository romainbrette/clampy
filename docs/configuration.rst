Configuration
=============

Examples of configuration files are given in the `setup` folder.

Setting up the acquisition board
--------------------------------

Currently, only National instruments boards are implemented, based on NI-DAQmx (`nidaqmx` package).
Create a board object as follows:

.. code:: Python

    from clampy import *
    from clampy.setup.units import *
    board = NI()
    board.sampling_rate = 40000*Hz

The module `clampy.setup.units` defines the ISI values of a few common units. For example, `Hz` is 1
and `mV` is `0.001`.

Channels are specified by giving names to a physical channel, with a gain:

.. code:: Python

    board.set_analog_input('I', channel=0, gain=100*mV/nA)
    board.set_analog_output('Ic', channel=0, gain=100*mV/nA)
    board.set_digital_input('trigger_in', channel=0)
    board.set_digital_output('trigger_output', channel=0)

The gain is specified as voltage at the board divided by the corresponding quantity measured or controlled
by the amplifier.
In the example above, a 1 nA signal appears as 100 mV at the board.
Optionally, an analog input can be given `min` and `max` values (for the measured quantities, i.e., in nA for
this example).

It is possible to set aliases, for example:

.. code:: Python

    board.set_aliases(reading='I', command='Ic')

Here the name `reading` can be used to mean `I`.

Configuring analog amplifiers
-----------------------------

An analog amplifier is configured by setting the gains according to the amplifier specifications.
Be careful of the convention for gains: `clampy` always uses board / amplifier,
amplifier specifications may use a different convention for input and output channels.

Gains are given for the Axoclamp 2B and the Axoclamp 900A. Use as follows:

.. code:: Python

    from clampy.devices.gains.axoclamp2b import gains # or axoclamp900A
    board.set_analog_input('Im', channel=0, gain=gains(0.1)['Im'])

Here `gains` is a function of H, which is a specification of the headstage (proportional to its gain),
and `gains(H)` is a dictionary of gains for the different channels.
See the examples of configuration files in the `setup` package.

Configuring digital amplifiers
------------------------------

There is partial support for two digital amplifiers: Axoclamp 900A and Multiclamp (700A and 700B).
Digital amplifiers can be set up in the same way as analog amplifiers by setting the gains manually.
Additionally, gains can be obtained by software:

.. code:: Python

    amplifier = AxoClamp900A()
    board.set_analog_output('Ic1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
    board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
    board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
    amplifier.configure_scaled_outputs(board, 'output1', 'output2')

Here, we call `Ic1` the signal coming out from amplifier channel `I-CLAMP 1`, which is connected to board
channel 0. The gain will be automatically obtained from the amplifier.
The next two commands do the same for the scaled outputs, which on this amplifier can be routed to
different signals. The final command configures the scaled outputs on the board so that when trying to
read for example the signal `10V1`, the amplifier is configured to route that signal to one of the scaled
outputs, and `10V1` then acts as an alias for that signal.

Common practice
---------------

A simple practice is to put all the configuration commands in an `init_rig.py` file, then import it
when running an acquisition script (`from init_rig import *`).
In this way, it is possible to easily switch to another configuration, for example a virtual configuration
running a model (`from init_rig_model import *`).
Alternatively, when using version control on different computers, the `init_rig.py` file can be specific of each
computer (not shared), so that the code runs on different configurations.
