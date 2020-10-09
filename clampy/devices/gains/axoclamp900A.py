'''
Gains of the Axoclamp 900A

gains(H) returns a dictionary of gains for Headstage Current Gain H
'''

__all__ = ['gains']

mV = 0.001
volt = 1.
nA = 1e-9

gains = lambda H : {'Ic' : 10./H * mV/nA,
                    'Vc' : 1./(20 * mV / volt),
                    'DIV10I2' : 10*mV/nA,
                    'V' : 10*mV/mV,
                    'I' : 100*mV/nA}
# then there are software-controlled gains that multiply these
