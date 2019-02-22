from pylab import *
from clampy.setup.units import *
from init_rig import *

__all__ = ['do_analysis']

def do_analysis(path):
    # Loading
    Ic = loadtxt(path+'/Steps/I.txt') * nA
    V = loadtxt(path+'/Steps/V.txt') * mV
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
    do_analysis('.')
