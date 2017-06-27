'''
Model cells to test scripts.

These are meant to be used as amplifiers.
'''
from analysis.trace_analysis import lowpass

__all__ = ['RCCell']

class RCCell(object):
    '''
    An RC circuit.
    '''
    def __init__(self, R, C, dt):
        self.R = R
        self.C = C
        self.dt = dt

    def acquire(self, *inputs, **outputs):
        '''
        Send commands and acquire signals.

        Parameters
        ----------
        inputs
            A list of input variables to acquire. From: V, I, Ve (electrode potential)
            A maximum of two inputs.
        outputs
            A dictionary of commands. From: V, I.
            Only one command!
        '''
        # A few checks
        if len(inputs)>2:
            raise IndexError("Not more than two signals can be measured.")
        if len(outputs)!=1:
            raise IndexError('Only one command signal can be passed.')

        outputname = outputs.keys()[0]
        results = dict()
        if outputname == 'I': # Current clamp
            results['V'] = self.R*lowpass(outputs['I'], tau = self.R*self.C, dt = self.dt)
            results['I'] = outputs['I']
        elif outputname == 'V': # Voltage clamp
            results['I'] = outputs['V']/self.R
            results['V'] = outputs['V']
        else:
            raise IndexError("Output command must be I or V.")

        # Fills in other values
        results['Ve'] = results['V']
        results['Vext'] = results['V']
        results['100V'] = results['V']
        results['Ic'] = results['I']
        results['Iext'] = results['I']

        if len(inputs) == 1:
            return results[inputs[0]]
        else:
            return [results[x] for x in inputs]
