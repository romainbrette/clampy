'''
Axon Digidata 1322A

TODO:
* Catch exceptions
* Set gains
* In acquire: fill in output buffers
* Gains of Axoclamp 2B (depends on headstage)
'''
from axDD132x import *
from ctypes import *
from ctypes.wintypes import *
from board import *

__all__ = ['Digidata1322A']


class Digidata1322A(Board):
    '''
    Axon Digidata 1322A acquisition board
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
        data = DD132X_CalibrationData()
        DD132X_GetCalibrationData(self.dev, byref(data), byref(pnError))
        self.ADC_gain = float(data.dADCGainRatio) # conversion from analog to digital
        self.ADC_offset = int(data.nADCOffset)
        self.DAC_gain = [data.adDACGainRatio[i] for i in range(16)]
        self.DAC_offset = [data.anDACOffset[i] for i in range(16)]
        #print data.wNumberOfDACs

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
        Board.set_analog_input(self, name, channel, gain)

    def set_analog_output(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (volt/input unit)
        '''
        Board.set_analog_output(self, name, channel, gain)

    def set_digital_output(self, name, channel=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_digital_output(self, name, channel)

    def acquire(self, inputs, outputs, dt = None):
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
            protocol.anAOChannels[i] = self.analog_output[name]
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
        #print "Starting acquisition"
        while DD132X_IsAcquiring(self.dev):
            pass

        # Return input measurements (presumably interlaced?)
        return [hostbuffer[i::nchannels] for i in range(len(inputs))]


if __name__ == '__main__':
    from brian2 import * # for units

    board = Digidata1322A()
    # These are Axoclamp 2B settings
    board.set_analog_input('Im', channel = 0, gain = 0.1*volt/nA)
    board.set_analog_input('Vm', channel = 1, gain = 10*mV/mV)
    board.set_analog_output('Vc', channel = 0, gain= 0.02*volt/volt)
    board.set_analog_output('Ic', channel = 1, gain = 1*nA/volt)

    Vm = board.acquire(('Vm',), {'Ic' : zeros(100)}, dt = 0.05*ms)

    print Vm