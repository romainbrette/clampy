'''
Acquisition board

TODO:
* Acquisition with no output command, or with no input
* Direct read/write of single value
* sampling_rate could be a property.
* make private variables for gain etc, and maybe rename get_gain to gain.
* error checking (e.g. assigning the same channel twice)
* Add min and max for channels
'''
import numpy as np
import time

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
        self.alias = dict() # dictionary of aliases (mapping from alias to channel name)
        self.sampling_rate = None # could be a property
        self.reset_clock()

    def reset_clock(self):
        self.init_time = time.time()

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

    def set_virtual_input(self, name, channel = None, deviceID=None, select=None):
        '''
        Sets a virtual analog input.

        Parameters
        ----------
        name : identifier of the input for the board
        channel : channel name or list of names
        select : device function, called with the device ID of the selected channel
        deviceID : an identifier for the device that is connected to this input.
        '''
        self.virtual_input[name] = channel
        self.select_function[name] = select
        self.deviceID[name] = deviceID

    def set_virtual_output(self, name, channel = None, deviceID=None, select=None):
        '''
        Sets a virtual analog output.

        Parameters
        ----------
        name : identifier of the output for the board
        channel : channel name or list of names
        select : device function, called with the device ID of the selected channel
        deviceID : an identifier for the device that is connected to this output.
        '''
        self.virtual_output[name] = channel
        self.select_function[name] = select
        self.deviceID[name] = deviceID

    def set_aliases(self, **aliases):
        '''
        Defines aliases for channels.

        Arguments
        ---------
        aliases : dictionary with keys = aliases, values = channel names
        '''
        for alias, channel in aliases.iteritems():
            self.alias[alias] = channel

    def get_alias(self, alias):
        '''
        Returns the original channel name of the alias.
        If not an alias, returns the same name.
        '''
        if alias in self.alias:
            return self.alias[alias]
        else:
            return alias

    def substitute_aliases(self, x):
        '''
        Substitute aliases in x, which can be a string, a list or a dictionary
        '''
        if isinstance(x, str):
            return self.get_alias(x)
        elif isinstance(x, list) or isinstance(x, tuple):
            return [self.get_alias(name) for name in x]
        elif isinstance(x, dict):
            return dict(zip(self.substitute_aliases(x.keys()),x.values()))

    def get_gain(self, name):
        '''
        Returns the gain of the named channel
        '''
        name = self.get_alias(name)
        deviceID = self.deviceID[name]
        if deviceID is None: # in this case the gain is a fixed number
            return self.gain[name]
        else: # call the device to get the gain
            return self.gain[name](deviceID) # for virtual channels however, it should probably be the ID of the physical channel

    def save(self, filename, acquisition_time=None, **signals):
        '''
        Saves signals to the file `filename`.

        Parameters
        ----------
        filename : name of the file. The extension should be npz.
        signals : dictionary of signals
        acquisition_time : time at acquisition start
        '''
        # Add time variable
        one_signal = signals.values()[0]
        t = np.arange(len(one_signal))/self.sampling_rate
        signals['t'] = t
        # We could other information, like gains etc
        signals['acquisition_time'] = acquisition_time

        f = open(filename, 'wb')
        np.savez_compressed(f, **signals)
        f.close()

    def acquire(self, *inputs, **kwd):
        '''
        Acquires scaled signals and returns scaled measurements (with appropriate gains).
        Also handles virtual channels.

        Parameters
        ----------
        inputs : list of input names (= measurements)
        kwd : keywords, either an output signal (key = output channel name, value = array)
              or one of the following keywords.

        save : filename to save the data

        Returns
        -------
        Values of inputs, as list of arrays or single array (if just one input).
        '''
        # Parse keywords
        filename = None
        analog_outputs={}
        digital_outputs={}
        for keyword,value in kwd.iteritems():
            if keyword=='save':
                filename=value
            elif self.get_alias(keyword) in self.analog_output:
                analog_outputs[keyword]=value
            elif self.get_alias(keyword) in self.digital_output:
                digital_outputs[keyword]=value
            else:
                raise AttributeError('{} is not an output channel'.format(keyword))

        # Substitute aliases
        digital_outputs=self.substitute_aliases(digital_outputs)

        # 1. Configure virtual channels
        # a. Dictionary of allocated channels
        all_channels = self.analog_input.keys() + self.analog_output.keys()
        allocated=dict.fromkeys(all_channels, False)
        # b. Virtual inputs
        analog_inputs = []
        for I in inputs:
            I = self.get_alias(I)
            if I in self.virtual_input:
                channel = self.virtual_input[I]
                selected_channel = None
                # Allocate a channel
                if isinstance(channel,str) and not allocated[channel]:  # Single channel
                    allocated[channel] = True
                    selected_channel = channel
                else:
                    for C in channel:
                        if allocated[C] is False:
                            allocated[C] = True
                            selected_channel = C
                            break
                if selected_channel is None:
                    raise IOError('Could not allocate a physical channel to virtual channel {}'.format(I))
                analog_inputs.append(selected_channel)
                # Call the device to make the selection # ID of the signal, then ID of the physical wiring
                self.select_function[I](self.deviceID[I], self.deviceID[selected_channel])
            else:
                analog_inputs.append(I)
        # c. Virtual outputs (not considered yet)

        # 2. Get the correct gains
        gain = dict()
        for I in analog_inputs:
            gain[I] = self.get_gain(I)
        for O in analog_outputs:
            O = self.get_alias(O)
            gain[O] = self.get_gain(O)

        # 3. Check that all output arrays have the same length
        nsamples = [len(output) for output in analog_outputs.values()]
        if not all([nsample==nsamples[0] for nsample in nsamples]):
            raise Exception('Output arrays have different lengths.')

        # 4. Scale output gains
        raw_analog_outputs = dict() # maps physical channel numbers to signal waveforms
        names, values = analog_outputs.keys(), analog_outputs.values()
        for name, value in zip(names, values):
            aliased_name = self.get_alias(name)
            gain = self.get_gain(name)
            analog_outputs[name] = value * gain
            raw_analog_outputs[self.analog_output[aliased_name]] = value * gain

        raw_digital_outputs = dict()
        for name, value in digital_outputs.iteritems():
            aliased_name = self.get_alias(name)
            raw_digital_outputs[self.digital_output[aliased_name]] = value

        # 5. Acquire
        input_channels = [self.analog_input[name] for name in analog_inputs]
        acquisition_time = time.time()-self.init_time
        results = self.acquire_raw(analog_inputs=input_channels, analog_outputs=raw_analog_outputs,
                                   digital_outputs=raw_digital_outputs)

        # 6. Scale input gains
        scaled_results = [value/self.get_gain(name) for name,value in zip(analog_inputs,results)]

        # 7. Save
        if filename is not None:
            signals = dict()
            for name, value in zip(inputs, scaled_results):
                signals[name] = value
            signals.update(analog_outputs)
            signals.update(digital_outputs)
            self.save(filename, acquisition_time=acquisition_time, **signals)

        # Return
        if len(inputs)==1: # not a list, single element
            return scaled_results[0]
        else:
            return scaled_results

    def acquire_raw(self, analog_inputs=[], analog_outputs={}, digital_inputs=[], digital_outputs={}):
        '''
        Acquires raw signals in volts, not scaled.
        Virtual channels are not handled.
        This is typically the method that needs to be rewritten for a specific board.

        Parameters
        ----------
        analog_inputs : list of analog input channels (indexes) (= measurements)
        analog_outputs : dictionary of analog output channels (key = output channel index, value = array)
        digital_inputs : list of digital input channels (indexes) (= measurements)
        digital_outputs : dictionary of digital output channels (key = output channel index, value = array)

        Returns
        -------
        Values for inputs as a list of arrays, first analog inputs, then digital inputs.
        '''
        n = len(analog_outputs.values()[0])
        return [np.ones(n) for _ in analog_inputs] # for testing purposes


if __name__ == '__main__':
    import numpy as np

    def gain_function(deviceID):
        if deviceID=='OUTPUT1':
            return 12
        else:
            return 13

    def select_function(signalID, channelID):
        print(signalID,channelID)

    board = Board()
    board.set_analog_input('output1', channel=0, deviceID='OUTPUT1', gain = gain_function)
    board.set_analog_input('output2', channel=1, deviceID='OUTPUT2', gain = gain_function)
    board.set_analog_output('Ic', channel=0, gain=10)
    board.set_virtual_input('V', channel=('output1','output2'), deviceID='VAMP', select = select_function)
    board.set_virtual_input('I', channel=('output1','output2'), deviceID='IAMP', select = select_function)

    print(board.acquire('I','V',Ic = np.array([1,2,3,4.])))
