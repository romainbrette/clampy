'''
Initializes data acquisition on the rig.
This is specific of the hardware configuration.
'''
from clampy import *
from clampy.setup.units import *

board = NI()

dt = 0.1 * ms
board.sampling_rate = float(1 / dt)
board.set_analog_input('output1', channel=0)
board.set_analog_input('I1', channel=1)
board.set_analog_output('Ic1', channel=1)

amp = AxoClamp900A()
amp.configure_board(board, output1="output1", I1='I1', Ic1='Ic1')
