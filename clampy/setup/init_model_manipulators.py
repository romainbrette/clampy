'''
Initializes for model running mode with fake manipulators and pressure controller.
'''
from brian2 import *
from clampy.brianmodels import *
from holypipette.devices.pressurecontroller import FakePressureController
from holypipette.devices.manipulator import *

dt = 0.1*ms
board = RC_and_electrode(Ce = 3*pF)
amplifier = board
board.set_aliases(Ic='I', Vc='V', V1='V', V2='V', I_TEVC='I')

# Fake pressure controller
pressure = FakePressureController()

# Fake stage/manipulators
controller = FakeManipulator(min=[-4096, -4096, -1000, -4096, -4096, -1000, -4096, -4096, -1000],
                             max=[4096, 4096, 1000, 4096, 4096, 1000, 4096, 4096, 1000])
controller.x[:3] = [-50, 10, 500]
controller.x[3:6] = [100, -25, 500]
controller.x[8] = 520
stage = ManipulatorUnit(controller, [7, 8])
units = [ManipulatorUnit(controller, [1, 2, 3]), ManipulatorUnit(controller, [4, 5, 6])]
