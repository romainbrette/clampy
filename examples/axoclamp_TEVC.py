'''
Two-electrode voltage clamp with the Axoclamp 900A
'''
from clampy import *
from pylab import *
from clampy.signals import *

ms = 0.001
pA = 1e-12
mV = 0.001
volt = 1
nA = 1e-9
dt = 0.1 * ms

amplifier = AxoClamp900A()
#amplifier.reset()

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
board.set_analog_output('Ic1', channel=0, deviceID='Ic1', gain=amplifier.get_gain)
board.set_analog_output('Ic2', channel=1, deviceID='Ic2', gain=amplifier.get_gain)
board.set_analog_input('I2', channel=2, deviceID='I', gain=amplifier.get_gain)
board.set_analog_output('Vc', channel=2, deviceID='Vc', gain=amplifier.get_gain)

board.set_virtual_input('V1', channel=('output1', 'output2'), deviceID=SIGNAL_ID_10V1,
                        select=amplifier.set_scaled_output_signal)
board.set_virtual_input('V2', channel=('output1', 'output2'), deviceID=SIGNAL_ID_10V2,
                        select=amplifier.set_scaled_output_signal)
board.set_virtual_input('I2', channel=('output1', 'output2'), deviceID=SIGNAL_ID_DIV10I2,
                        select=amplifier.set_scaled_output_signal)

amplifier.TEVC()

Vc = sequence([constant(10 * ms, dt) * 0 * mV,
               constant(60 * ms, dt) * 30 * mV,
               constant(130 * ms, dt) * 0 * mV])
V, I = board.acquire('V1','I2', Vc=Vc) # current is always injected through headstage 2

# Plotting
figure()
subplot(211)
t = dt*arange(len(Vc))
plot(t/ms, array(I) / nA)
ylabel('Current (nA)')
subplot(212)
plot(t/ms, array(V) / mV)
ylabel('Voltage (mV)')
xlabel('Time (ms)')
title('Response to a voltage pulse')

show()
