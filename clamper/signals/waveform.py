'''
Basic waveforms
'''
from numpy import *
try:
    from brian2.units import Quantity
except ImportError:
    pass

__all__ = ['sequence', 'constant', 'ramp']

def sequence(signal_list):
    # Concatenates signals and uses the units of the first element
    try:
        unit = Quantity(1,signal_list[0].dimensions)
    except:
        unit = 1
    return hstack(signal_list)*unit

def constant(duration, dt):
    # Constant 1
    return ones(int(duration/dt))

def ramp(duration, dt):
    # Ramps from 0 to 1
    return linspace(0, 1, int(duration/dt))
