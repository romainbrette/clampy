'''
Initializes data acquisition on the rig, with the two headstages swapped.
This is specific of the hardware configuration.
'''
from clampy import *
from clampy.devices.gains.axoclamp2b import gains
from clampy.setup.units import *

board = NI()

board.set_analog_output('I2', channel=1, gain=gains(0.1)['ExtME1'])  # Current clamp command
board.set_analog_output('I', channel=2, gain=gains(1)['ExtME2'])  # Current clamp command
board.set_analog_input('V2', channel=1, gain=gains(0.1)['10Vm'])  # Vm
board.set_analog_input('V', channel=3, gain=gains(1)['V2'])

board.set_aliases(I='Ic1', I1='Ic1', I2='Ic2', Vc='V', V='V1', I_TEVC='Ic2')

dt = 0.1 * ms
board.sampling_rate = 1. / dt

#amplifier = board
