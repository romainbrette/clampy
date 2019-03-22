from pylab import *
from clampy.setup.units import *
from clampy import *

#from init_rig import *

__all__ = ['do_analysis']

def do_analysis(path):
    ms = 1e-3
    mV = 1e-3
    # Loading
    info = load_info(path+'/current_clamp_experiment.info')
    dt = info['dt']
    Ic = loadtxt(path+'/Steps/I.txt')
    V = loadtxt(path+'/Steps/V.txt')
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
