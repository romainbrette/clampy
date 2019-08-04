'''
Basic waveforms
'''
from numpy import *
try:
    from brian2.units import Quantity
except ImportError:
    pass

__all__ = ['sequence', 'constant', 'ramp', 'ticks']

def sequence(signal_list):
    # Concatenates signals and uses the units of the first element
    try:
        unit = Quantity(1,signal_list[0].dimensions)
    except:
        unit = 1
    return hstack(signal_list)*unit

def constant(duration, dt, dtype=float):
    # Constant 1
    return ones(int(duration/dt), dtype=dtype)

def ramp(duration, dt):
    # Ramps from 0 to 1
    return linspace(0, 1, int(duration/dt))

def ticks(duration, dt, rate, t0=0.):
    '''
    Ticks (True/False) regularly placed at specified rate,
    synchronized at t0.
    '''
    trigger = constant(duration, dt, dtype=bool)
    trigger[:] = False
    T = int(1. / rate / dt)
    # Align with t0
    T1 = int((t0) / dt) - T * arange(0, int((t0) * rate))
    T2 = int((t0) / dt) + T * arange(1,int((duration - t0) * rate))
    trigger_times = hstack((T1, T2))
    trigger[trigger_times] = True
    return trigger
