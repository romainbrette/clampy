'''
Axoclamp 900A oscilloscope with gamepad control

See: https://github.com/romainbrette/manipulator/blob/master/gamepad.py

TODO:
* Replace sliders by number entries

Figure updating is really slow!
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
from time import sleep
import time

# Initialization
ms = 0.001
pA = 1e-12
mV = 0.001
volt = 1
nA = 1e-9
dt = 0.05 * ms
Mohm = 1e6

# Gamepad reader
class GamepadReader(threading.Thread):
    def __init__(self, gamepad):
        self.event_container = []
        self.gamepad = gamepad
        super(GamepadReader, self).__init__()
        self.terminated = False
        self.X = 0.
        self.RX = 0.

    def run(self):
        while not self.terminated:
            event = self.gamepad.read()[0] # This blocks the thread
            #if event.code in ['ABS_X', 'ABS_Y', 'ABS_Z', 'ABS_RZ']:
            if event.code == 'ABS_X':
                self.X = event.state/32768.
                if abs(self.X) < 0.1:
                    self.X = 0.
            elif event.code == 'ABS_RX':
                self.RX = event.state/32768.
                if abs(self.RX) < 0.1:
                    self.RX = 0.
            self.event_container.append(event)

    def stop(self):
        self.terminated = True

'''
Because the gamepad reader works in blocking mode (could it be changed?)
we need another thread to update the GUI while the joystick is moved, for example.
'''
class GUIUpdater(threading.Thread):
    def __init__(self, gamepad):
        self.gamepad = gamepad
        super(GUIUpdater, self).__init__()
        self.terminated = False

    def run(self):
        while not self.terminated:
            if abs(self.gamepad.X) > 0.1:
                capacitance = capa_button.val
                capacitance += 0.01 * self.gamepad.X * capa_range.dValMax
                if capacitance > capa_button.valmax:
                    capacitance = capa_button.valmax
                elif capacitance < capa_button.valmin:
                    capacitance = capa_button.valmin
                capa_button.set_val(capacitance)
            if abs(self.gamepad.RX) > 0.1:
                VC_gain = gain_button.val
                VC_gain += gamepad.RX * 20.
                gain_button.set_val(VC_gain)

    def stop(self):
        self.terminated = True

# Amplifier and board
amplifier = AxoClamp900A()
amplifier.reset()

board = NI()
board.sampling_rate = float(1./dt)
board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
board.set_analog_output('Ic1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
board.set_analog_output('Ic2', channel=1, deviceID='I-CLAMP 2', gain=amplifier.get_gain)
board.set_analog_output('Vc', channel=2, deviceID='V-CLAMP', gain=amplifier.get_gain)

amplifier.configure_scaled_outputs(board, 'output1', 'output2')

board.set_aliases(V='10V1', V1='10V1', V2='10V2', I_TEVC='DIV10I2')

amplifier.current_clamp(0)
amplifier.set_cap_neut_enable(True, 0)

gamepad = GamepadReader(inputs.devices.gamepads[0])
gamepad.start()

gui_updater = GUIUpdater(gamepad)
gui_updater.start()

# Oscilloscope

I0 = -0.2*nA
T0 = 10*ms
T1 = 30*ms
T2 = 20*ms
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

capa_range = amplifier.get_cap_neut_range(0)
ax_capa = plt.axes([0.5, 0.075, 0.3, 0.05])
capa_button = Slider(ax_capa,'Capacitance', capa_range.dValMin, capa_range.dValMax, 0)
capa_button.on_changed(change_capa)
capacitance = 0.

ax_gain = plt.axes([0.5, 0.125, 0.3, 0.05])
gain_button = Slider(ax_gain,'Gain', 20, 500, 20)
gain_button.on_changed(change_gain)
VC_gain = 20.

ax_lag = plt.axes([0.5, 0.175, 0.3, 0.05])
lag_button = Slider(ax_lag,'Lag', 0, 100, 0)
lag_button.on_changed(change_lag)
VC_lag = 0.

display_title()

def update(i):
    global capacitance, VC_gain, current_clamp

    # Gamepad control
    for event in gamepad.event_container:
        if (event.code == 'BTN_WEST') and (event.state == 1): # X
            amplifier.set_pipette_offset_lock(False,0)
            amplifier.auto_pipette_offset(0)
        elif (event.code == 'BTN_SOUTH') and (event.state == 1): # A
            mode_button.set_active(0)
        elif (event.code == 'BTN_EAST') and (event.state == 1): # B
            mode_button.set_active(1)
    gamepad.event_container[:] = []

    # Acquisition
    if current_clamp:
        t1 = time.time()
        V = board.acquire('V', Ic1=Ic)
        t2 = time.time()
        print(t2-t1)
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

anim = animation.FuncAnimation(fig,update,interval=0)

show()

gui_updater.stop()
gamepad.stop()
