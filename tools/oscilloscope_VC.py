'''
An oscilloscope showing the current response to a pulse
'''
import collections
import os
import datetime
import time

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


class SessionRecorder(object):
    def __init__(self, basedir):
        self.basedir = basedir
        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)
        self.start_time_real = None
        self.start_time_counter = None
        self.recordings = collections.defaultdict(list)

    def start_recording(self):
        self.start_time_real = datetime.datetime.now()
        self.start_time_counter = time.time()

    def stop_recording(self):
        formatted_time = self.start_time_real.strftime('%H:%M:%S')
        basename = 'recording_' + formatted_time
        for name, values in self.recordings.items():
            filename = basename + '_' + name + '.tsv'
            with open(os.path.join(self.basedir, filename), 'wt') as f:
                for timepoint, value in zip(*values):
                    f.write('{}\t{}\n'.format(timepoint, value))

    def record(self, name, sample_start, values):
        if name not in self.recordings:
            self.recordings[name] = ([], [])
        time_points = (sample_start - self.start_time_counter) + np.arange(len(values))*(dt/second)
        self.recordings[name][0].extend(time_points)
        self.recordings[name][1].extend(values)

experiment_start = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
recorder = SessionRecorder(os.path.join('./data',
                                        '{}_voltage_clamp'.format(experiment_start)))

recording = False
def record_callback(event):
    global recording
    recording = not recording
    if recording:
        recorder.start_recording()
        record_button.label.set_text('Stop')
    else:
        recorder.stop_recording()
        record_button.label.set_text('Record')


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
ax_record = plt.axes([0.81, 0.9, 0.1, 0.075])
record_button = Button(ax_record, 'Record')
record_button.on_clicked(record_callback)

def update(i):
    sample_start = time.time()
    I, V_hold = amplifier.acquire('I', 'V', V=Vc*factor)
    if recording:
        recorder.record('I', sample_start, I)
        recorder.record('V_hold', sample_start, V_hold)
        recorder.record('V_command', sample_start, [factor])
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
