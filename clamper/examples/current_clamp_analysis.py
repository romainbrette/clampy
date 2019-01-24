from pylab import *
from clamper.setup.units import *
from init_rig import *

__all__ = ['do_analysis']

def do_analysis(Ic, V):
    # Plotting
    figure()
    t = dt*arange(len(Ic))
    for Vi in V:
        plot(t/ms, array(Vi) / mV)
    xlabel('Time (ms)')
    ylabel('Voltage (mV)')
    title('Response to current pulses')
    show()

if __name__ == '__main__':
    # Loading
    Ic = loadtxt('Steps/I.txt') * nA
    V = loadtxt('Steps/V.txt') * mV
    do_analysis(Ic, V)
