'''
Gains of the Axoclamp 2B

gains(H) returns a dictionary of gains for Headstage Current Gain H
'''

__all__ = ['gains']

mV = 0.001
volt = 1.
nA = 1e-9

gains = lambda H : {'Im' : 10./H * mV/nA,
                    'I2' : 10./H * mV/nA,
                    '0.1xI2' : 1./H * mV/nA,
                    'ExtVC' : 1./(20*mV/volt),
                    'ExtME1' : 1./(10.*H * nA/volt),
                    'ExtME2': 1./(10. * H * nA / volt),
                    '10Vm' : 10 * mV/mV,
                    'V2' : 1* mV/mV}
