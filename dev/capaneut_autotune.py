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

controller.set_mode(1, 'IC')
controller.select_tab('I1')
controller.set_capneut(0)
controller.detect_oscillation('reduce')

C = 0

while C<50:
    print(C)
    Ic = steps([(0 * nA, 50*ms),
                (-.1*nA, 50*ms),
                (0 * nA, 200*ms)], dt)
    board.acquire('V2', Ic2=Ic, save=join(data_path, 'data{:03d}.txt.gz'.format(int(C))))

    controller.set_capneut(C)
    if not controller.is_capaneut_on(): # assuming it will be stopped if there is an oscillation
        break
    C += 1
    #time.sleep(0.1)
