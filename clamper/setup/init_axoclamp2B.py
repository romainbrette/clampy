'''
Initializes data acquisition on the rig.
This is specific of the hardware configuration.
'''
from clamper import *
from clamper.devices.gains.axoclamp2b import gains
from clamper.setup.units import *

board = NI()

board.set_analog_output('I', channel=1, gain=gains(0.1)['ExtME1'])  # Current clamp command
board.set_analog_output('I2', channel=2, gain=gains(1)['ExtME2'])  # Current clamp command
#board.set_analog_output('V', channel=2, gain=gains(1)['ExtVC']) # Voltage clamp command
board.set_analog_input('V', channel=1, gain=gains(0.1)['10Vm'])  # Vm
board.set_analog_input('V2', channel=3, gain=gains(1)['V2'])
#board.set_analog_input('I', channel=3, gain=gains(0.1)['Im'])

dt = 0.1 * ms
board.sampling_rate = 1. / dt

amplifier = board
