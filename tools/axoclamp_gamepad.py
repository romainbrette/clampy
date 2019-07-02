'''
Axoclamp 900A oscilloscope with gamepad control

See: https://github.com/romainbrette/manipulator/blob/master/gamepad.py

TODO:
* Refactor gamepad.

Figure updating is really slow! (under Windows but no Mac, it seems)
Solution (?): use blitting
'''
from __future__ import print_function
from clampy import *
from pylab import *
from clampy.signals import *
from init_rig import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import time

# Import gamepad package
gamepad_found = True
try:
    from clampy.gamepad import *
except ModuleNotFoundError: # I had to change the module name because of a conflict with Tensorflow
        gamepad_found = False

# Amplifier and board
#amplifier.reset()  # Erase previous tunings

amplifier.current_clamp(0)
try:
    amplifier.set_cap_neut_enable(True, 0)
except AttributeError:
    pass

if gamepad_found:
    gamepad = GamepadReader()
    gamepad.start()

    gamepad_integrator = GamepadIntegrator(gamepad)
    gamepad_integrator.start()

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

# Plots
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)

ax1 = plt.subplot(211)
t = dt*arange(len(Ic))
ax1.set_xlim(0,max(t/ms))
ax1.set_ylim(auto=True)
lineV, = ax1.plot(t/ms,0*t)
ax1.set_ylabel('V (mV)')

ax2 = plt.subplot(212)
ax2.set_xlim(0,max(t/ms))
lineI, = ax2.plot(t/ms,0*t)
ax2.set_ylim(auto=True)
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('I (nA)')

status_text = ax1.text(0.5, 0.9, 'Axoclamp oscilloscope', transform=ax1.transAxes, horizontalalignment='center')

# Autoadjust button
def autoadjust_callback(event):
    autoadjust = autoadjust_checkbox.get_status()[0]
    if autoadjust:
        ax.set_ylim(auto=True)
    else:
        ax.set_ylim(auto=False)

ax_checkbox = plt.axes([0.7, 0.025, 0.15, 0.125], frameon=False)
autoadjust_checkbox = CheckButtons(ax_checkbox, ['auto'], [True])
autoadjust_checkbox.on_clicked(autoadjust_callback)

current_clamp = True

# Set amplifier parameters
try:
    capa_range = amplifier.get_cap_neut_range(0)
    capa_min = capa_range.dValMin
    capa_max = capa_range.dValMax
except AttributeError:
    capa_min, capa_max = -0.2, 36.

capacitance = 0.
VC_gain = 20.
VC_lag = 0.

last_update = time.time()

def update(i):
    global current_clamp, last_update

    # Gamepad control
    if gamepad_found:
        # Buttons
        for event in gamepad.event_container:
            if (event.code == 'BTN_WEST') and (event.state == 1): # X
                amplifier.set_pipette_offset_lock(False,0)
                amplifier.auto_pipette_offset(0)
            elif (event.code == 'BTN_SOUTH') and (event.state == 1): # A
                current_clamp = True
                amplifier.current_clamp(0)
                amplifier.current_clamp(1)
                status_text.set_text('Current clamp')
            elif (event.code == 'BTN_EAST') and (event.state == 1): # B
                current_clamp = False
                amplifier.TEVC()
                amplifier.set_external_command_enable(True, 1)
            status_text.set_text('TEVC')
        gamepad.event_container[:] = []

        # Joysticks
        if gamepad_integrator.has_changed('X'):
            capacitance = 0.01 * gamepad_integrator.X * capa_max
            if capacitance > capa_max:
                capacitance = capa_max
                gamepad_integrator.X = capacitance/(0.01*capa_max)
            elif capacitance < capa_min:
                capacitance = capa_min
                gamepad_integrator.X = capacitance / (0.01 * capa_max)
            amplifier.set_cap_neut_enable(True, 0)
            amplifier.set_cap_neut_level(capacitance, 0)
            status_text.set_text('C = {:.1f} pF'.format(capacitance))

        if gamepad_integrator.has_changed('RX'):
            VC_gain = gamepad_integrator['RX'] * 20.
            amplifier.set_loop_gain(VC_gain, 1)
            status_text.set_text('gain = {}'.format(int(VC_gain)))

    # Acquisition
    if current_clamp:
        V = board.acquire('V', Ic1=Ic)
        I = Ic
    else:
        V, I = board.acquire('V', 'I_TEVC', Vc=Vc)

    # Plot
    lineV.set_ydata(V/mV)
    lineI.set_ydata(I/nA)

    # Autoadjust
    t = time.time()
    if t-last_update>1.:
        autoadjust = autoadjust_checkbox.get_status()[0]
        if autoadjust: # could be done once in a while
            for axis in (ax1,ax2):
                axis.set_ylim(auto=True)
                # recompute the ax.dataLim
                axis.relim()
                # update ax.viewLim using the new dataLim
                axis.autoscale_view()
        last_update = t

    return lineV,

anim = animation.FuncAnimation(fig,update,interval=0)

show()

if gamepad_found:
    gamepad_integrator.stop()
    gamepad.stop()
