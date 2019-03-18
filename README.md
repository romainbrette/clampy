# clampy
This is a Python package to control a patch-clamp amplifier.
It works with National Instruments acquision boards. Three amplifiers are implemented:
* Axoclamp 2B (just the gains)
* Multiclamp 700B
* Axoclamp 900A

It can be interfaced with the neural simulator Brian to run the protocols on a model.

A typical acquisition protocol reads:

    V = board.acquire('V', Ic=my_pulse)
    
where `my_pulse` is an array representing the current waveform.
