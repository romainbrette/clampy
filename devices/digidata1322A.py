'''
Axon Digidata 1322A

TODO:
* Catch exceptions
'''
from axDD132x import *
from ctypes import *
from ctypes.wintypes import *
from board import *

__all__ = ['Digidata1322A']


class Digidata1322A(Board):
    '''
    A generic acquisition board
    '''
    def __init__(self):
        Board.__init__(self)

        # Initialization
        ifo = DD132X_Info()
        pnError = c_int()
        nDevs = DD132X_FindDevices(byref(ifo), 1, byref(pnError))
        if (nDevs < 1):
            raise ('No DigiData Device found')

        # Open the device; dev is device handler
        self.dev = DD132X_OpenDevice(ifo.byAdaptor, ifo.byTarget, byref(pnError))

        # Calibration

    def __del__(self):
        pnError = c_int()

        DD132X_CloseDevice(self.dev, byref(pnError))

    def set_analog_input(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_analog_input(name, channel, gain)

    def set_analog_output(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_analog_output(name, channel, gain)

    def set_digital_output(self, name, channel=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_digital_output(name, channel)

    def acquire(self, inputs, outputs, dt):
        '''
        Acquires signals with sampling interval dt.
        The program returns only once acquisition is finished.

        Parameters
        ----------
        inputs : list of input names
        outputs : dictionary of output signals (key = output channel name, value = array with units)
        dt : sampling interval
        '''
        # Check that all output arrays have the same length
        nsamples = [len(output) for output in outputs.values()]
        if not all([nsample==nsamples[0] for nsample in nsamples]):
            raise Exception('Output arrays have different lengths.')
        nsamples = nsamples[0]
        nchannels = len(inputs) + len(outputs)

        # Make an acquisition protocol
        protocol = DD132X_Protocol()
        protocol.dSampleInterval = c_double(dt*1e6)  # in us
        protocol.dwFlags = 1  # stop on terminal count
        protocol.eTriggering = DD132X_StartImmediately
        protocol.uAIChannels = len(inputs)
        for i in range(len(inputs)):
            protocol.anAIChannels[i] = self.analog_input[inputs[i]]
        protocol.uAOChannels = len(outputs)
        for i,name in enumerate(outputs.keys()):
            protocol.uAOChannels[i] = self.analog_output[name]
        protocol.uOutputPulseType = DD132X_NoOutputPulse

        # Allocate data buffers
        # We make only one buffer to simplify
        # But we could make a list of buffers for longer durations
        hostbuffer = (ADC_VALUE * nsamples * nchannels)()

        buffer = DATABUFFER()
        buffer.uNumSamples = nsamples * nchannels
        buffer.uFlags = 0
        buffer.pnData = hostbuffer
        buffer.psDataFlags = None
        buffer.pNextBuffer = None  # pointer(buffer)
        buffer.pPrevBuffer = None  # pointer(buffer)
        protocol.pAIBuffers = pointer(buffer)
        protocol.uAIBuffers = 1
        protocol.uChunksPerSecond = 20
        protocol.uTerminalCount = LONGLONG(nsamples * nchannels)

        # Start acquisition
        pnError = c_int()
        DD132X_SetProtocol(self.dev, byref(protocol), byref(pnError))
        DD132X_StartAcquisition(self.dev, byref(pnError))

        # Wait until finished
        while DD132X_IsAcquiring(self.dev):
            pass

        # Return input measurements (presumably interlaced?)
        return [hostbuffer[i::nchannels] for i in range(len(inputs))]
