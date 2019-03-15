'''
Acquisition board

TODO:
* I note that, actually, it is not necessary to distinguish between input, output, digital, analog.
  A single method would be sufficient.
* sampling_rate could be a property.
'''
__all__ = ['Board']

class Board:
    '''
    A generic acquisition board
    '''
    def __init__(self):
        self.analog_input = dict() # channel number
        self.analog_output = dict()
        self.digital_input = dict()
        self.digital_output = dict()
        self.gain = dict()
        self.deviceID = dict()
        self.virtual_input = dict()
        self.virtual_output = dict()
        self.select_function = dict() # signal selection function for virtual channels
        self.sampling_rate = None # could be a property

    def set_analog_input(self, name, channel=None, gain=None, deviceID=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor, for an analog input.

        Parameters
        ----------
        name : identifier of the input for the board
        channel : channel number (starting from 0)
        gain : conversion factor (volt/input unit), or a function returning the conversion factor,
               called with deviceID as argument.
        deviceID : an identifier for the device that is connected to this input.
        '''
        self.analog_input[name] = channel
        self.gain[name] = gain
        self.deviceID[name] = deviceID

    def set_analog_output(self, name, channel=None, gain=None, deviceID=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        name : identifier of the output for the board
        channel : channel number (starting from 0)
        gain : conversion factor (output unit/volt), or a function returning the conversion factor,
               called with deviceID as argument.
        deviceID : an identifier for the device that is connected to this output.
        '''
        self.analog_output[name] = channel
        self.gain[name] = gain
        self.deviceID[name] = deviceID

    def set_digital_input(self, name, channel=None, deviceID=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        name : identifier of the input for the board
        channel : channel number (starting from 0)
        deviceID : an identifier for the device that is connected to this input.
        '''
        self.digital_input[name] = channel
        self.deviceID[name] = deviceID

    def set_digital_output(self, name, channel=None, deviceID=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        name : identifier of the output for the board
        channel : channel number (starting from 0)
        deviceID : an identifier for the device that is connected to this output.
        '''
        self.digital_output[name] = channel
        self.deviceID[name] = deviceID

    def set_virtual_input(self, name, channel = None, select=None):
        '''
        Sets a virtual input.

        Parameters
        ----------
        name : identifier of the input for the board
        channel : channel number or list of numbers
        select : device function, called with the device ID of the selected channel
        '''
        self.virtual_input[name] = channel
        self.select_function[name] = select

    def set_virtual_output(self, name, channel = None, select=None):
        '''
        Sets a virtual output.

        Parameters
        ----------
        name : identifier of the output for the board
        channel : channel number or list of numbers
        select : device function, called with the device ID of the selected channel
        '''
        self.virtual_output[name] = channel
        self.select_function[name] = select

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
