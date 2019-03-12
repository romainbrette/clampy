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
board.set_analog_output('Ic2', channel=1)
board.set_analog_output('V', channel=2)


amp = AxoClamp900A()
amp.configure_board(board, output1="output1", output2='output2', Ic1="Ic1", Ic2='Ic2')

#amp.set_cache_enable(True)

#amp.reset()

amp.current_clamp(0)
print('Capacitance: {}'.format(amp.get_cap_neut_level(0))) # doesn't work?
#amp.set_scaled_output_signal(2,0)  # SIGNAL_ID_10V1 (could be mon?)
#amp.set_external_command_enable(True,0,1)
amp.set_bridge_enable(True, 0)
amp.set_bridge_resistance(50e6, 0) # this doesn't seem to work
#amp.set_bridge_lock(True,0)
#amp.auto_bridge_balance(0)
print('Bridge resistance in Mohm: {}'.format(amp.get_bridge_resistance(0)/1e6))
#amp.switch_holding(False,0)

#amp.set_bridge_enable(True, 0)
#amp.set_bridge_lock(True, 0)
#range = amp.get_bridge_range(0)
#print(range.dValMin,range.dValMax,range.nValMin,range.nValMax)

#amp.set_cap_neut_enable(True,0)
#amp.set_cap_neut_level(1e-12,0)

amp.current_clamp(1)
#amp.switch_holding(False,1)
#amp.set_bridge_enable(True, 1)
#amp.set_bridge_resistance(50e6, 1) # this doesn't seem to work
#print('Bridge resistance in Mohm: {}'.format(amp.get_bridge_resistance(1)/1e6))


#amp.auto_bridge_balance(0)
#print(amp.get_bridge_resistance(0))

#amp.set_scaled_output_signal_gain(1.5,0)
#print(amp.get_scaled_output_signal_gain(0))

#amp.TEVC()

#exit(0)

Ic = zeros(int(1000 * ms / dt))
Ic[int(130 * ms / dt):int(330 * ms / dt)] += 1000 * pA

#amp.set_bridge_balance(True)
#amp.auto_bridge_balance(0) # doesn't work
#print (Rs / 1e6)

amp.auto_pipette_offset(0)
print("Pipette offset 1: {}".format(amp.get_pipette_offset(0)))
amp.auto_pipette_offset(1)
print("Pipette offset 2: {}".format(amp.get_pipette_offset(1)))

#amp.set_bridge_lock(False, 0)

V1, V2 = amp.acquire('V1', 'V2', I1=Ic)
#V1, V2 = amp.acquire('V1', 'V2', I2=Ic)

#print('Bridge resistance in Mohm: {}'.format(amp.get_bridge_resistance(0)/1e6))

subplot(211)
plot(array(V1) / (mV), 'r')
plot(array(V2) / (mV), 'b')
subplot(212)
plot(Ic / pA, 'r')
#plot(I1 / pA, 'b')
show()
