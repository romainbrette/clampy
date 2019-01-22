'''
An oscilloscope showing the voltage response to a pulse

TODO:
* maybe add slider or so for current amplitude and duration
* calculate resistance, V0 etc
'''
from clamper import *
from pylab import *
from clamper.signals import *
import os
from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

swap = False # Swap the two electrodes

I0 = -0.3*nA
T0 = 10*ms
T1 = 100*ms
T2 = 100*ms
Ic = sequence([constant(T0, dt) * 0 * nA,
               constant(T1, dt) * I0,
               constant(T2, dt) * 0 * nA])

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
plt.xlabel('Time (ms)')
plt.ylabel('V (mV)')
resistance_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

t = dt*arange(len(Ic))
xlim(0,max(t/ms))
ylim(-150,100)
line, = plot(t/ms,0*t)


def display_title():
    if swap:
        ax.set_title("Electrode Current")
    else:
        ax.set_title("Electrode Other")

def callback(event):
    global swap
    swap = not swap
    display_title()

ax_button = plt.axes([0.81, 0.05, 0.1, 0.075])
switch_button = Button(ax_button, 'Switch')
switch_button.on_clicked(callback)

display_title()

def update(i):
    if swap:
        V = board.acquire('V2', I2=Ic)
    else:
        V = board.acquire('V', I=Ic)
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
