"""
Analysis of cell parameters
"""
from electrode_compensation import full_kernel
from numpy import arange, exp, array, sqrt
from scipy import optimize

__all__ = ['passive_properties_from_noise']

def passive_properties_from_noise(I, V, kernel_duration = 0.5, dt = 1e-4, R0 = 50e6, C0 = 300e-12):
    '''
    Calculates R, C and V0 from response to noise.
    For optimal results, use electrode_compensation.calibration_noise() to generate the noise.

    Arguments
    ---------
    I : noise current
    V : voltage trace
    kernel_duration : duration of the impulse response in second
    dt : time step in second

    Returns
    -------
    R : membrane resistance
    C : membrane capacitance
    V0 : resting potential
    '''
    I, V = array(I), array(V)  # remove units if present
    Km, V0 = full_kernel(V, I, int(kernel_duration/dt), full_output=True)
    # Fit of the kernel to find the membrane time constant
    t = arange(len(Km))
    f = lambda params: params[0] * exp(-params[1] ** 2 * t) - Km
    p0 = dt/C0
    p1 = sqrt(dt/(R0*C0))
    p, _ = optimize.leastsq(f, array([p0, p1]))
    #Km = p[0] * exp(-p[1] ** 2 * t)
    tau = dt / (p[1] ** 2)
    R = p[0]/(p[1] ** 2)
    C = tau/R

    return R, C, V0
