'''
A simple current clamp script

-2 to 2 nA for 60 ms
'''

from clamper import *
from pylab import *
from clamper.brianmodels import *

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
    dt = .1 * ms
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

Ic = zeros(int(10/dt))*pA
V = amp.acquire('V', I=Ic)

t = dt*arange(len(Ic))

savetxt('V.txt',V)

plot((t[::5])/ms, array(V)[::5] / mV)
show()
