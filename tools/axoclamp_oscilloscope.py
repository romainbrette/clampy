'''
An oscilloscope showing the voltage response to a pulse
for the Axoclamp 900A.
'''
from clampy import *
from pylab import *
from clampy.signals import *
from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, Slider

I0 = -0.2*nA
T0 = 10*ms
T1 = 100*ms
T2 = 100*ms
Ic = sequence([constant(T0, dt) * 0 * nA,
               constant(T1, dt) * I0,
               constant(T2, dt) * 0 * nA])

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.4)
plt.xlabel('Time (ms)')
plt.ylabel('V (mV)')
resistance_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

t = dt*arange(len(Ic))
xlim(0,max(t/ms))
ylim(-150,100)
line, = plot(t/ms,0*t)


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
    if mode_button.value_selected == 'CC':
        amplifier.current_clamp(0)
    else: # TEVC
        amplifier.TEVC()

def change_bridge(event):
    amplifier.set_bridge_balance(bridge_button.val,0)

def change_capa(event):
    pass

def change_gain(event):
    pass

def change_lag(event):
    pass

ax_mode = plt.axes([0.05, 0.025, 0.2, 0.125], frameon=False)
mode_button = RadioButtons(ax_mode, ['CC', 'TEVC'])
mode_button.on_clicked(change_mode)

ax_bridge = plt.axes([0.5, 0.025, 0.3, 0.05])
bridge_button = Slider(ax_bridge,'Bridge', 0, 100, 0)
bridge_button.on_changed(change_bridge)
ax_capa = plt.axes([0.5, 0.075, 0.3, 0.05])
capa_button = Slider(ax_capa,'Capacitance', 0, 30, 0)
capa_button.on_changed(change_capa)
ax_gain = plt.axes([0.5, 0.125, 0.3, 0.05])
gain_button = Slider(ax_gain,'Gain', 0, 1000, 0)
gain_button.on_changed(change_gain)
ax_lag = plt.axes([0.5, 0.175, 0.3, 0.05])
lag_button = Slider(ax_lag,'Lag', 0, 100, 0)
lag_button.on_changed(change_lag)

display_title()

def update(i):
    V = amplifier.acquire('V', I=Ic)
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
