'''
Initializes data acquisition on the rig.
This is specific of the hardware configuration.
'''
from clampy import *
from clampy.setup.units import *
from holypipette.devices.pressurecontroller import OB1
from holypipette.devices.manipulator import *

board = NI()

dt = 0.1 * ms
board.sampling_rate = float(1 / dt)
board.set_analog_input('primary', channel=0)
board.set_analog_input('secondary', channel=1)
board.set_analog_output('command', channel=0)

amplifier = MultiClampChannel()
amplifier.configure_board(board, primary='primary', secondary='secondary', command='command')

controller = LuigsNeumann_SM10(stepmoves=False)
stage = ManipulatorUnit(controller, [7, 8])
units = [ManipulatorUnit(controller, [1, 2, 3]), ManipulatorUnit(controller, [4, 5, 6])]

pressure = None
try:
    pressure = OB1()
except Exception as ex:
    print('Cannot use pressure controller: ' + str(ex))
