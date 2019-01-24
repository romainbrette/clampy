'''
An oscilloscope showing the current response to a pulse
'''
from clamper import *
from pylab import *
from clamper.signals import *
from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

swap = False # Swap the two electrodes

V0 = - 10.*mV
T0 = 50*ms
T1 = 10*ms
T2 = 50*ms
Vc = sequence([constant(T0, dt) * 0 * mV,
               constant(T1, dt) * V0,
               constant(T2, dt) * 0 * mV])

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
plt.xlabel('Time (ms)')
plt.ylabel('V (mV)')
resistance_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

t = dt*arange(len(Vc))
xlim(0,max(t/ms))
ylim(-10,10)
line, = plot(t/ms,0*t)

def callback(event):
    y = line.get_ydata()
    ax.set_ylim(min(y),max(y))

ax_button = plt.axes([0.81, 0.05, 0.1, 0.075])
switch_button = Button(ax_button, 'Adjust')
switch_button.on_clicked(callback)

def update(i):
    I = amplifier.acquire('I', V=Vc)
    ## Calculate offset and resistance
    I0 = median(I[:int(T0/dt)]) # calculated on initial pause
    Ipeak = median(I[int((T0+2*T1/3.)/dt):int((T0+T1)/dt)]) # calculated on last third of the pulse
    R = V0/(Ipeak-I0)
    # Plot
    line.set_ydata(I/pA)
    resistance_text.set_text('{:.1f} MOhm'.format(R/Mohm))
    return line,

anim = animation.FuncAnimation(fig,update)

show()
