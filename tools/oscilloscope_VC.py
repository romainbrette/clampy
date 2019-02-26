'''
An oscilloscope showing the current response to a pulse
'''
from clampy import *
from pylab import *
from clampy.signals import *
from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons, TextBox

swap = False # Swap the two electrodes

V0 = 1*mV  # This will be scaled with a factor later, assuming that the sequence
           # contains only 0 or V0!
T0 = 50*ms
T1 = 10*ms
T2 = 50*ms
Vc = sequence([constant(T0, dt) * 0 * mV,
               constant(T1, dt) * V0,
               constant(T2, dt) * 0 * mV])

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
plt.xlabel('Time (ms)')
plt.ylabel('I (pA)')
resistance_text = ax.text(0.05, 0.9, '', transform=ax.transAxes)

t = dt*arange(len(Vc))
xlim(0, max(t/ms))
ylim(auto=True)
line, = plot(t/ms, 0*t/ms)


def adjust_callback(event):
    y = line.get_ydata()
    ax.set_ylim(1.05*min(y), 1.05*max(y))


def autoadjust_callback(event):
    autoadjust = autoadjust_checkbox.get_status()[0]
    if autoadjust:
        ax.set_ylim(auto=True)
    else:
        ax.set_ylim(auto=False)


factor = -10.  # clamped voltage in mV
def value_callback(text):
    global factor
    if stim_selection.value_selected == 'off':
        return
    try:
        factor = float(text)
    except (TypeError, ValueError) as ex:
        # Not a parseable number
        print('Invalid value: {} !'.format(text))


def selection_callback(event):
    global factor
    if stim_selection.value_selected == 'on':
        try:
            factor = float(stim_value.text)
        except (TypeError, ValueError) as ex:
            print('Invalid value: {} !'.format(text))
    else:
        factor = 0.
    print('selection factor: {}'.format(factor))


ax_button = plt.axes([0.81, 0.05, 0.1, 0.075])
adjust_button = Button(ax_button, 'Adjust')
adjust_button.on_clicked(adjust_callback)
ax_checkbox = plt.axes([0.7, 0.025, 0.15, 0.125], frameon=False)
autoadjust_checkbox = CheckButtons(ax_checkbox, ['auto'], [True])
autoadjust_checkbox.on_clicked(autoadjust_callback)
ax_selection = plt.axes([0.05, 0.025, 0.2, 0.125], frameon=False)
stim_selection = RadioButtons(ax_selection, ['on', 'off'])
stim_selection.on_clicked(selection_callback)
ax_stim_value = plt.axes([0.26, 0.05, 0.1, 0.075])
stim_value = TextBox(ax_stim_value, 'VC (mV):', '-10')
stim_value.on_submit(value_callback)


def update(i):
    I = amplifier.acquire('I', V=Vc*factor)
    ## Calculate offset and resistance
    if abs(factor) > 0:
        I0 = median(I[:int(T0/dt)]) # calculated on initial pause
        Ipeak = median(I[int((T0+2*T1/3.)/dt):int((T0+T1)/dt)]) # calculated on last third of the pulse
        R = V0/(Ipeak-I0)
        resistance_text.set_text('{:.1f} MOhm'.format(R / Mohm))
    else:
        resistance_text.set_text('[no clamp]')
    # Plot
    line.set_ydata(I/pA)
    autoadjust = autoadjust_checkbox.get_status()[0]
    if autoadjust:
        ax.set_ylim(auto=True)
        # recompute the ax.dataLim
        ax.relim()
        # update ax.viewLim using the new dataLim
        ax.autoscale_view()
    return line,

anim = animation.FuncAnimation(fig, update)

show()
