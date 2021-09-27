'''
Basic waveforms

The duration argument should perhaps become obsolete
'''
from numpy import *
try:
    from brian2.units import Quantity
except ImportError:
    pass

__all__ = ['sequence', 'constant', 'ramp', 'ticks', 'steps']

def steps(step_list, dt=1):
    # List of constants steps, specified as (x, t)
    # where t is the end time
    t2 = [t for _, t in step_list]
    t1 = [0]+t2[:-1]
    x = [a for a, _ in step_list]
    dtype = type(x[0])
    if dtype is not bool:
        dtype = float
    return sequence([xi*constant(dt=dt, t1=t1i, t2=t2i, dtype=dtype) for t1i, t2i, xi in zip(t1, t2, x)])

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
    TODO: there is a missing trigger at the onset, some rounding issue
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
