Tools
=====

NI pulse generator
------------------
The script `ni_pulse_generator.py` is a GUI to produce regular pulses through
a NI board counter.
The channel is a counter channel. This is not the same as a digital channel.
Typically, the counter needs first to routed to the right PFI output channel.
This can be done with the following instruction:

.. code:: Python

    board.connect_counter_to_PFI(counter_channel, PFI_channel)

