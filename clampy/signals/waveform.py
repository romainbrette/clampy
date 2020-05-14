'''
Basic waveforms

The duration argument should perhaps become obsolete
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

def constant(duration=None, dt=1, dtype=float, t1=None, t2=None):
    # Constant 1
    if t1 is not None:
        return ones(int(t2 / dt) - int(t1/dt), dtype=dtype)
    else:
        return ones(int(duration/dt), dtype=dtype)

def ramp(duration=None, dt=1, dtype=float, t1=None, t2=None):
    # Ramps from 0 to 1
    if t1 is not None:
        return linspace(0, 1, int(t2 / dt)-int(t1/dt), dtype=dtype)
    else:
        return linspace(0, 1, int(duration/dt), dtype=dtype)

def ticks(duration=None, dt=1, rate=None, t0=0., t1=None, t2=None):
    '''
    Ticks (True/False) regularly placed at specified rate,
    synchronized at t0.
    '''
    trigger = constant(duration=duration, dt=dt, dtype=bool, t1=t1, t2=t2)
    trigger[:] = False
    T = int(1. / rate / dt)
    # Align with t0
    T1 = int((t0) / dt) - T * arange(0, int((t0) * rate))
    T2 = int((t0) / dt) + T * arange(1,int((duration - t0) * rate))
    trigger_times = hstack((T1, T2))
    trigger[trigger_times] = True
    return trigger
