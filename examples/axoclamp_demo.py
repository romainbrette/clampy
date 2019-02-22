"""
Demonstrates the use of the Axoclamp 900A
"""
from clampy import *
from pylab import *
from clampy.signals import *
#from init_rig import *
import time

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

amp = AxoClamp900A()
amp.configure_board(board, output1="output1", output2='output2', Ic1='Ic1')

amp.current_clamp(0)
amp.set_bridge_balance(True, 0)
amp.set_bridge_resistance(10e6, 0)
print(amp.get_bridge_resistance(0))
#amp.auto_bridge_balance(0)
#print(amp.get_bridge_resistance(0))

#amp.set_scaled_output_signal_gain(1.5,0)
#print(amp.get_scaled_output_signal_gain(0))

#amp.TEVC()

#exit(0)

Ic = zeros(int(1000 * ms / dt))
Ic[int(130 * ms / dt):int(330 * ms / dt)] += 500 * pA
Vc = zeros(int(1000 * ms / dt))
Vc[int(130 * ms / dt):int(330 * ms / dt)] = 20 * mV
#amp.set_bridge_balance(True)
#Rs = amp.auto_bridge_balance()
#print (Rs / 1e6)

Vm = amp.acquire('V1', I1=Ic)

#print("Resistance", R / 1e6)

subplot(211)
plot(array(Vm) / (mV))
subplot(212)
plot(Ic / pA)
show()
