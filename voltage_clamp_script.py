'''
A simple voltage clamp script

-100 to 20 mV for 60 ms
'''

from devices import *
from pylab import *
from brianmodels import *

model = True

if model:
    from brian2 import *
    eqs = 'dV/dt = (500*Mohm*I-V)/(20*ms) : volt'
    dt = 0.1*ms
    amp = BrianExperiment(eqs, namespace = {}, dt=dt)
else:
    ms = 0.001
    pA = 1e-12
    mV = 0.001
    volt = 1
    nA = 1e-9
    dt = 0.1 * ms
    pF = 1e-12
    MOhm = 1e6

    board = NI()
    board.sampling_rate = float(1/dt)
    board.set_analog_input('primary', channel=0)
    board.set_analog_input('secondary', channel=1)
    board.set_analog_output('command', channel=0)

    amp = MultiClampChannel()
    amp.configure_board(board, primary='primary', secondary='secondary', command='command')

    amp.set_bridge_balance(True)
    Rs = amp.auto_bridge_balance()
    print "Bridge resistance:",Rs / 1e6

ntrials = 20
Vc = zeros(int(200 * ms / dt))*volt
I = []
for ampli in linspace(-100,20,ntrials)*mV:
    print ampli
    Vc[int(10 * ms / dt):int(70 * ms / dt)] = ampli
    I.append(amp.acquire('I', V=Vc))

t = dt*arange(len(Vc))

savetxt('data2.txt',array(Vc)/mV)

for Ii in I:
    plot(t/ms, array(Ii) / mV)
show()
