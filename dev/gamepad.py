'''
Displays gamepad inputs
'''
from __future__ import print_function
import inputs

gamepad = inputs.devices.gamepads[0]

while True:
    event = gamepad.read()[0]
    # events = get_gamepad() # same as devices.gamepads[0].read()
    # for event in events:
    print(event.ev_type, event.code, event.state)

