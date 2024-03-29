'''
Automatic capacitance neutralization
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

Ic = steps([(0 * nA, 50 * ms),
            (-.1 * nA, 100 * ms),
            (0 * nA, 200 * ms)], dt)

C = 0

while C<100:
    print(C)
    V2 = board.acquire('V2', Ic2=Ic, save=join(data_path, 'data{:03d}.txt.gz'.format(int(C))))

    controller.set_capneut(C*.1)
    if not controller.is_capaneut_on(): # assuming it will be stopped if there is an oscillation
        break
    C += 1

    #time.sleep(0.1)
