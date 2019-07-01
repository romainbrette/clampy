'''
Displays gamepad inputs
'''
from __future__ import print_function
import inputs_gamepad as inputs
#import inputs
from time import sleep

gamepad = inputs.devices.gamepads[0]

while True:
    events = gamepad.read()
    # events = get_gamepad() # same as devices.gamepads[0].read()
    for i,event in enumerate(events):
        print(i,event.ev_type, event.code, event.state)
    sleep(1)

'''
BTN_START 1, 0
BTN_SELECT
BTN_WEST/NORTH/EAST/SOUTH 1/0    = XYBA
ABS_HAT0X -1/0/1  = cross
ABS_HAT0Y -1/0/1
BTN_TL/BTN_TR 1/0   left right finger
ABS_Z/ABS_RZ 0-255   second left right finger
ABS_X/ABS_Y/ABS_RX/ABS_RY   -32... + 32...
'''
