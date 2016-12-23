'''
Axon Digidata 1322A

TODO:
* Output not working (but it was working before!)
* Does not seem to work when input is large (more than 1500 points?)
* Catch exceptions
* Set gains
* Gains of Axoclamp 2B (depends on headstage)
* Unit checks
'''
from axDD132x import *
from ctypes import *
from ctypes.wintypes import *
from board import *
from time import time, sleep
from numpy import array
from brian2 import volt

__all__ = ['Digidata1322A']


verbose = True

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
        if verbose:
            print "Calibrating"
        data = DD132X_CalibrationData()
        DD132X_GetCalibrationData(self.dev, byref(data), byref(pnError))

        self.ADC_gain = float(data.dADCGainRatio) # conversion from analog to digital
        self.ADC_offset = int(data.nADCOffset)
        self.DAC_gain = [data.adDACGainRatio[i] for i in range(16)]
        self.DAC_offset = [data.anDACOffset[i] for i in range(16)]
        # print data.wNumberOfDACs,self.ADC_gain, self.ADC_offset, self.DAC_gain,self.DAC_offset

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

        # Input buffer
        hostbuffer = (ADC_VALUE * (nsamples * len(inputs)))()
        buffer = DATABUFFER()
        buffer.uNumSamples = nsamples * len(inputs)
        buffer.uFlags = 0
        buffer.pnData = hostbuffer
        buffer.psDataFlags = None
        buffer.pNextBuffer = None  # pointer(buffer)
        buffer.pPrevBuffer = None  # pointer(buffer)

        protocol.pAIBuffers = pointer(buffer)
        protocol.uAIBuffers = 1

        # Output buffer
        hostbuffer_out = (ADC_VALUE * (nsamples * len(outputs)))()
        #hostbuffer_out = (ADC_VALUE * 1440000)()
        # Fill buffer
        for i,name in enumerate(outputs.keys()):
            hostbuffer_out[i::len(outputs)] = array(outputs[name]*32767/(10*volt)/self.gain[name],dtype = int16)

        buffer_out = DATABUFFER()
        buffer_out.uNumSamples = nsamples * len(outputs)
        buffer_out.uFlags = 0
        buffer_out.pnData = hostbuffer_out
        buffer_out.psDataFlags = None
        buffer_out.pNextBuffer = None  # pointer(buffer)
        buffer_out.pPrevBuffer = None  # pointer(buffer)

        protocol.pAOBuffers = pointer(buffer_out)
        protocol.uAOBuffers = 1


        protocol.uChunksPerSecond = 20
        protocol.uTerminalCount = LONGLONG(nsamples * len(inputs))
        #### NOT CLEAR WHAT IS BEING COUNTED!!

        # Start acquisition
        pnError = c_int()
        DD132X_SetProtocol(self.dev, byref(protocol), byref(pnError))
        DD132X_StartAcquisition(self.dev, byref(pnError))

        if pnError:
            print "arrrgh"
            return [array([]) for _ in range(len(inputs))]

        # Wait until finished
        if verbose:
            print "Starting acquisition"
        count = LONGLONG(0)
        t = time()
        while (count.value<nsamples * len(inputs)):
            DD132X_GetAcquisitionPosition(self.dev, byref(count), byref(pnError))

        DD132X_StopAcquisition(self.dev, byref(pnError))

        # Return input measurements (presumably interlaced?)
        return [array(hostbuffer[i::len(inputs)]) * 10. * volt/32767/self.gain[input] for i,input in enumerate(inputs)]


if __name__ == '__main__':
    from brian2 import volt, mV, nA, ms, pA, zeros # for units
    from pylab import *

    board = Digidata1322A()
    # These are Axoclamp 2B settings
    board.set_analog_input('Im', channel = 0, gain = 0.1*volt/nA)
    board.set_analog_input('Vm', channel = 1, gain = 10*mV/mV)
    board.set_analog_input('Im2', channel = 2, gain = 1*volt/nA)
    board.set_analog_input('V2', channel = 3, gain = 1)
    board.set_analog_output('Vc', channel = 0, gain= 0.02*volt/volt)
    board.set_analog_output('Ic', channel = 1, gain = 1*nA/volt)

    dt = 0.5*ms
    #Ic = ones(int(300*ms/dt))*10*pA
    #Ic[int(30*ms/dt):int(230*ms/dt)] += 500*pA
    Ic = ones(20)*10*pA
    Ic[5:15] = 510*pA

    Vm, = board.acquire(('Vm',), {'Ic' : Ic}, dt = dt)

    del board

    #subplot(311)
    plot(Vm/mV)
    #subplot(312)
    #plot(Im/pA)
    #subplot(313)
    #plot(V2/mV)
    show()
