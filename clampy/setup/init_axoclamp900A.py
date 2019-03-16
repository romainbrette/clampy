'''
Initializes data acquisition on the Axoclamp 900A.
'''
from clampy import *
from clampy.setup.units import *

dt = 0.1 * ms

amplifier = AxoClamp900A()

board = NI()
board.sampling_rate = float(1 / dt)
board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
board.set_analog_output('Ic1', channel=0, deviceID='Ic1', gain=amplifier.get_gain)
board.set_analog_output('Ic2', channel=1, deviceID='Ic2', gain=amplifier.get_gain)
board.set_analog_input('I2', channel=2, deviceID='I', gain=amplifier.get_gain)
board.set_analog_output('Vc', channel=2, deviceID='Vc', gain=amplifier.get_gain)

amplifier.configure_scaled_outputs(board, 'output1', 'output2')

board.set_aliases(V='10V1', V1='10V1', V2='10V2', I_TEVC='DIV10I2')
