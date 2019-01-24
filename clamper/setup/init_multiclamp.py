'''
Initializes data acquisition on the rig.
This is specific of the hardware configuration.
'''
from clamper import *
from clamper.setup.units import *

board = NI()

dt = 0.1 * ms
board.sampling_rate = float(1 / dt)
board.set_analog_input('primary', channel=0)
board.set_analog_input('secondary', channel=1)
board.set_analog_output('command', channel=0)

amplifier = MultiClampChannel()
amplifier.configure_board(board, primary='primary', secondary='secondary', command='command')
