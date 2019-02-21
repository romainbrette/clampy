"""
Demonstrates the use of the Axoclamp 900A
"""
from clamper import *
from pylab import *
from clamper.signals import *
from init_rig import *
import time

ms = 0.001
pA = 1e-12
mV = 0.001
volt = 1
nA = 1e-9
dt = 0.1 * ms

board = NI()
board.sampling_rate = float(10000.)
board.set_analog_input('primary', channel=0)
board.set_analog_input('secondary', channel=1)
board.set_analog_output('command', channel=1)

amp = AxoClampChannel()
amp.configure_board(board, primary='primary', secondary='secondary', command='command')

Ic = zeros(int(1000 * ms / dt))
Ic[int(130 * ms / dt):int(330 * ms / dt)] += 500 * pA
Vc = zeros(int(1000 * ms / dt))
Vc[int(130 * ms / dt):int(330 * ms / dt)] = 20 * mV
#amp.set_bridge_balance(True)
#Rs = amp.auto_bridge_balance()
#print (Rs / 1e6)

Vm, Im = amp.acquire('V', 'I', ICLAMP =Ic)

#print("Resistance", R / 1e6)

subplot(211)
plot(array(Vm) / (mV))
subplot(212)
plot(Im / pA)
show()