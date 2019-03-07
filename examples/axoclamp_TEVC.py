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

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('output1', channel=0)
board.set_analog_input('output2', channel=1)
board.set_analog_output('Ic1', channel=0)
board.set_analog_output('Ic2', channel=1)
board.set_analog_input('I2', channel=2)
board.set_analog_output('Vc', channel=2)

amplifier = AxoClamp900A()
amplifier.configure_board(board, output1="output1", output2='output2', Ic1='Ic1', Vc='Vc', I2='I2')

amplifier.TEVC() # optional

amplifier.set_external_command_enable(True,1)

Vc = sequence([constant(10 * ms, dt) * 0 * mV,
               constant(60 * ms, dt) * 30 * mV,
               constant(130 * ms, dt) * 0 * mV])
V, I = amplifier.acquire('V1','I2', V=Vc) # current is always injected through headstage 2

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
