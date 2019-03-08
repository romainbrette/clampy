'''
An oscilloscope showing the voltage response to a pulse
for the Axoclamp 900A.
'''
from clampy import *
from pylab import *
from clampy.signals import *
#from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, Slider

# Initialization
ms = 0.001
pA = 1e-12
mV = 0.001
volt = 1
nA = 1e-9
dt = 0.1 * ms
Mohm = 1e6

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('output1', channel=0)
board.set_analog_input('output2', channel=1)
board.set_analog_output('Ic1', channel=0)
board.set_analog_output('Ic2', channel=1)
board.set_analog_output('V', channel=2)
board.set_analog_output('Vc', channel=2)

amplifier = AxoClamp900A()
amplifier.configure_board(board, output1="output1", output2='output2', Ic1='Ic1', Ic2='Ic2',  Vc='Vc')
amplifier.current_clamp(0)

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

t = dt*arange(len(Ic))
xlim(0,max(t/ms))
ylim(-150,100)
line, = plot(t/ms,0*t)

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
    if current_clamp:
        V = amplifier.acquire('V1', I1=Ic)
    else:
        V = amplifier.acquire('V1', V=Vc)
    # Calculate offset and resistance
    V0 = median(V[:int(T0/dt)]) # calculated on initial pause
    Vpeak = median(V[int((T0+2*T1/3.)/dt):int((T0+T1)/dt)]) # calculated on last third of the pulse
    R = (Vpeak-V0)/I0
    # Plot
    line.set_ydata(V/mV)
    resistance_text.set_text('{:.1f} MOhm'.format(R/Mohm))
    return line,

anim = animation.FuncAnimation(fig,update)

show()
