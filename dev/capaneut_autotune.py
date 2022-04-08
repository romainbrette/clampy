'''
Automatic capacitance neutralization
'''
from clampy import *
from clampy.signals import *
from init_rig import *
from clampy.devices.axoclamp900A_gui import AxoclampController
import time

controller = AxoclampController()

controller.set_mode(1, 'IC')
controller.select_tab('I1')
controller.set_capneut(0)
controller.detect_oscillation('reduce')

C = 0

while True:
    controller.set_capneut(C)
    if not controller.is_capaneut_on(): # assuming it will be stopped if there is an oscillation
        break
    C += 1
    time.sleep(0.1)
