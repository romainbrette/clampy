'''
Initializes data acquisition on the Axoclamp 900A.
'''
from clampy import *
from clampy.setup.units import *

dt = 0.05 * ms

amplifier = AxoClamp900A()

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
board.set_analog_output('Ic1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
board.set_analog_output('Ic2', channel=1, deviceID='I-CLAMP 2', gain=amplifier.get_gain)
board.set_analog_output('Vc', channel=2, deviceID='V-CLAMP', gain=amplifier.get_gain)

amplifier.configure_scaled_outputs(board, 'output1', 'output2')

board.set_aliases(V='10V1', V1='10V1', V2='10V2', I_TEVC='DIV10I2', Ic='Ic2')

for channel in [0, 1]:
    amplifier.set_scaled_output_HPF(.5 / dt, channel)  # high-pass filter, cut-off at half sampling frequency (ok or maybe 1/4?)
