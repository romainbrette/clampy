'''
Axoclamp 900A oscilloscope with gamepad control

See: https://github.com/romainbrette/manipulator/blob/master/gamepad.py
'''
from __future__ import print_function
from clampy import *
from pylab import *
from clampy.signals import *
#from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, Slider
import threading
#import inputs
import inputs_gamepad as inputs

# Initialization
ms = 0.001
pA = 1e-12
mV = 0.001
volt = 1
nA = 1e-9
dt = 0.1 * ms
Mohm = 1e6

# Gamepad (do we really need to put this in a thread?)
class GamepadReader(threading.Thread):
    def __init__(self, gamepad):
        self.event_container = []
        self.gamepad = gamepad
        super(GamepadReader, self).__init__()

    def run(self):
        while True:
            event = self.gamepad.read()[0]
            #if event.code in ['ABS_X', 'ABS_Y', 'ABS_Z', 'ABS_RZ']:
            self.event_container.append(event)

# Amplifier and board
amplifier = AxoClamp900A()
amplifier.reset()

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
board.set_analog_output('Ic1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
board.set_analog_output('Ic2', channel=1, deviceID='I-CLAMP 2', gain=amplifier.get_gain)
board.set_analog_output('Vc', channel=2, deviceID='V-CLAMP', gain=amplifier.get_gain)

amplifier.configure_scaled_outputs(board, 'output1', 'output2')

board.set_aliases(V='10V1', V1='10V1', V2='10V2', I_TEVC='DIV10I2')

amplifier.current_clamp(0)

gamepad = GamepadReader(inputs.devices.gamepads[0])
gamepad.start()

# Oscilloscope

I0 = -0.2*nA
T0 = 10*ms
T1 = 100*ms
T2 = 100*ms
Ic = sequence([constant(T0, dt) * 0 * nA,
               constant(T1, dt) * I0,
               constant(T2, dt) * 0 * nA])

Vc = sequence([constant(T0, dt) * 0 * volt,
               constant(T1, dt) * 20*mV,
               constant(T2, dt) * 0 * volt])

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.4)
plt.xlabel('Time (ms)')
plt.ylabel('V (mV)')
resistance_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

subplot(211)
t = dt*arange(len(Ic))
xlim(0,max(t/ms))
ylim(-150,100)
lineV, = plot(t/ms,0*t)
ylabel('V (mV)')
subplot(212)
xlim(0,max(t/ms))
lineI, = plot(t/ms,0*t)
ylim(-5,5)
xlabel('Time (ms)')
ylabel('I (nA)')

current_clamp = True

def display_title():
    ax.set_title("Electrode Current")

def callback(event):
    global swap
    swap = not swap
    display_title()
    # Adjust y axis
    #y = line.get_ydata()
    #ax.set_ylim(min(y),max(y))

def change_mode(event):
    global current_clamp
    if mode_button.value_selected == 'CC':
        current_clamp = True
        amplifier.current_clamp(0)
        amplifier.current_clamp(1)
    else: # TEVC
        current_clamp = False
        amplifier.TEVC()
        amplifier.set_external_command_enable(True,1)

def change_bridge(event):
    amplifier.set_bridge_resistance(bridge_button.val*1e6,0)

def change_capa(event):
    amplifier.set_cap_neut_enable(True, 0)
    amplifier.set_cap_neut_level(capa_button.val,0)

def change_gain(event):
    amplifier.set_loop_gain(gain_button.val,1)

def change_lag(event):
    pass

ax_mode = plt.axes([0.05, 0.025, 0.2, 0.125], frameon=False)
mode_button = RadioButtons(ax_mode, ['CC', 'TEVC'])
mode_button.on_clicked(change_mode)

ax_bridge = plt.axes([0.5, 0.025, 0.3, 0.05])
bridge_button = Slider(ax_bridge,'Bridge', 0, 100, 0)
bridge_button.on_changed(change_bridge)

range = amplifier.get_cap_neut_range(0)
ax_capa = plt.axes([0.5, 0.075, 0.3, 0.05])
capa_button = Slider(ax_capa,'Capacitance', range.dValMin, range.dValMax, 0)
capa_button.on_changed(change_capa)

ax_gain = plt.axes([0.5, 0.125, 0.3, 0.05])
gain_button = Slider(ax_gain,'Gain', 20, 500, 20)
gain_button.on_changed(change_gain)

ax_lag = plt.axes([0.5, 0.175, 0.3, 0.05])
lag_button = Slider(ax_lag,'Lag', 0, 100, 0)
lag_button.on_changed(change_lag)

display_title()

def update(i):
    # Gamepad control
    for event in gamepad.event_container:
        print(event.code, event.state)
        '''
        if event.code == 'ABS_X':
            self.x = event.state / 32768.0
        elif event.code == 'ABS_Y':
            self.y = event.state / 32768.0
        elif event.code == 'ABS_Z':
            self.left_z = event.state / 255.
        elif event.code == 'ABS_RZ':
            self.right_z = event.state / 255.
        '''
    gamepad.event_container = []

    # Acquisition
    if current_clamp:
        V = board.acquire('V', Ic1=Ic)
        I = Ic
    else:
        V, I = board.acquire('V', 'I_TEVC', Vc=Vc)
    # Calculate offset and resistance
    V0 = median(V[:int(T0/dt)]) # calculated on initial pause
    Vpeak = median(V[int((T0+2*T1/3.)/dt):int((T0+T1)/dt)]) # calculated on last third of the pulse
    R = (Vpeak-V0)/I0
    # Plot
    lineV.set_ydata(V/mV)
    lineI.set_ydata(I/nA)
    resistance_text.set_text('{:.1f} MOhm'.format(R/Mohm))
    return lineV,

anim = animation.FuncAnimation(fig,update)

show()
