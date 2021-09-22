Introduction
============

Overview
--------
Clampy is a Python package to control acquision boards and electrophysiological
amplifiers. It works with National Instruments acquision boards. Three amplifiers are implemented:
* Axoclamp 2B (just the gains)
* Multiclamp 700B
* Axoclamp 900A

It can be interfaced with the neural simulator Brian to run the protocols on a model.

An example setup for the Axoclamp 900A and an NI board would be:

    amplifier = Axoclamp900A()
    board = NI()
    board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
    board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
    board.set_analog_output('Ic1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
    amplifier.configure_scaled_outputs(board, 'output1', 'output2')
    board.set_aliases(V='10V1', Ic='Ic1')

A typical acquisition protocol reads:

    amplifier.current_clamp()
    V = board.acquire('V', Ic=my_pulse)

where `my_pulse` is an array representing the current waveform.
