'''
Automatic capacitance neutralization
Basically a dichotomy algorithm.
- Set oscillation detection with disable.
- Start at 0, step size = C.
- C->C+step size
- If oscillation, C->previous C (-step size)
- step size -> step size/2

We want to set C = C*x (x=0.8 for example).

'''
from clampy import *
from clampy.signals import *
from init_rig import *
from clampy.devices.axoclamp900A_gui import AxoclampController
import time
from os.path import join

data_path = 'tuning'

controller = AxoclampController()

controller.set_mode(2, 'IC')
controller.select_tab('I2')
controller.set_capneut(0)
controller.detect_oscillation('disable')

step = 10. # pF
x = 0.8 # stop at x*optimal C
C = 0.

while step>C*(1-x)*.25:
    C += step
    controller.set_capneut(C)
    time.sleep(.4)
    if not controller.is_capaneut_on(): # assuming it will be stopped if there is an oscillation
        C -= step
    step = step*.5

print(C, step, C*x)
