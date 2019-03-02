'''
Acquisition board
'''
__all__ = ['Board']

class Board:
    '''
    A generic acquisition board
    '''
    def __init__(self):
        self.analog_input = dict()
        self.analog_output = dict()
        self.digital_output = dict()
        self.gain = dict()
        self.sampling_rate = None

    def set_analog_input(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (volt/input unit)
        '''
        self.analog_input[name] = channel
        self.gain[name] = gain

    def set_analog_output(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (output unit/volt)
        '''
        self.analog_output[name] = channel
        self.gain[name] = gain

    def set_digital_output(self, name, channel=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        channel : channel number (starting from 0)
        '''
        self.digital_output[name] = channel

    def acquire(self, *inputs, **outputs):
        '''
        Acquires signals with sampling interval dt.

        Parameters
        ----------
        inputs : list of input names
        outputs : dictionary of output signals (key = output channel name, value = array with units)
        dt : sampling interval
        '''
        # TODO: check units
        pass
