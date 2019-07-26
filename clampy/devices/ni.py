'''
National instruments board

There are a number of default values that we might need to look into.

Check this:
http://www.ni.com/tutorial/5409/en/
https://github.com/ni/nidaqmx-python/

For the NI USB 6343, analog output range is +-10 V, input ranges are:
    +-0.2 V, +-1 V, +-5 V, +-10 V
'''
from .board import *
import warnings
try:
    import nidaqmx
except ImportError:
    warnings.warn('NI-DAQmx could not be imported')
from numpy import zeros, array

class NI(Board):
    def __init__(self, device_name='Dev1', automatic_range_adjustment = False):
        Board.__init__(self)
        self.name = device_name
        self.automatic_range_adjustment = automatic_range_adjustment # if True, adjusts output range automatically

    def acquire_raw(self, analog_inputs=[], analog_outputs={}, digital_inputs=[], digital_outputs={}, input_range={}):
        '''
        Acquires raw signals in volts, not scaled.
        Virtual channels are not handled.

        Parameters
        ----------
        analog_inputs : list of analog input channels (indexes) (= measurements)
        analog_outputs : dictionary of analog output channels (key = output channel index, value = array)
        digital_inputs : list of digital input channels (indexes) (= measurements)
        digital_outputs : dictionary of digital output channels (key = output channel index, value = array)
        input_range : dictionary of (min, max) range for each input channel, in volt

        Returns
        -------
        Values for inputs as a list of arrays, first analog inputs, then digital inputs.
        '''
        dt = 1./self.sampling_rate
        if len(analog_outputs)>0:
            nsamples = len(analog_outputs.values()[0])
        else:
            nsamples = len(digital_outputs.values()[0])

        # Set the clock
        if len(analog_outputs)>0:
            clock = "/" + self.name + "/ao/SampleClock"
            clock_name='ao'
        elif len(digital_outputs)>0:
            clock = "/" + self.name + "/do/SampleClock"
            clock_name='do'
        elif len(analog_inputs)>0:
            clock = "/" + self.name + "/ai/SampleClock"
            clock_name='ai'
        elif len(digital_inputs)>0:
            clock = "/" + self.name + "/di/SampleClock"
            clock_name='di'

        # Read task
        # Analog input
        if len(analog_inputs)>0:
            input_task = nidaqmx.Task()
            for channel in analog_inputs:
                if channel in input_range:
                    min_val, max_val = input_range[channel]
                else:
                    min_val, max_val = -5., 5. # default values of add_ai_voltage_chan
                input_task.ai_channels.add_ai_voltage_chan(self.name+"/ai"+str(channel), min_val=min_val, max_val=max_val)
            if clock_name == 'ai':
                input_task.timing.cfg_samp_clk_timing(1. / dt, source=None, samps_per_chan=nsamples)
            else:
                input_task.timing.cfg_samp_clk_timing(1./dt, source=clock, samps_per_chan = nsamples)

        # Digital input
        if len(digital_inputs)>0:
            input_task_digital = nidaqmx.Task()
            for channel in digital_inputs: # 1 channel / line
                input_task_digital.di_channels.add_di_chan(self.name+"/line"+str(channel),
                                                   line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)
            if clock_name == 'di':
                input_task_digital.timing.cfg_samp_clk_timing(1. / dt, source=None, samps_per_chan=nsamples)
            else:
                input_task_digital.timing.cfg_samp_clk_timing(1./dt, source=clock, samps_per_chan = nsamples)

        # Write task
        # Analog output
        if len(analog_outputs)>0:
            output_task = nidaqmx.Task()
            #write_data = zeros((len(analog_outputs)+len(digital_outputs),nsamples)) # perhaps should be a list instead
            write_data = [None for _ in range(len(analog_outputs))]
            i=0
            for channel, value in analog_outputs.iteritems():
                # Range
                if self.automatic_range_adjustment:
                    min_val, max_val = min(value), max(value)+0.001 # adding 1 mV to avoid cases where min = max
                    output_task.ao_channels.add_ao_voltage_chan(self.name+"/ao"+str(channel), min_val=min_val, max_val=max_val)
                else:
                    output_task.ao_channels.add_ao_voltage_chan(self.name + "/ao" + str(channel))
                write_data[i]=value
                i=i+1
            if clock_name == 'ao':
                output_task.timing.cfg_samp_clk_timing(1. / dt, source=None, samps_per_chan=nsamples)
            else:
                output_task.timing.cfg_samp_clk_timing(1./dt, source=clock, samps_per_chan = nsamples)
            if i == 1:
                output_task.write(write_data[0]) #, timeout = nidaqmx.constants.WAIT_INFINITELY
            else:
                output_task.write(write_data) #, timeout = nidaqmx.constants.WAIT_INFINITELY

        # Digital output
        if len(digital_outputs)>0:
            output_task_digital = nidaqmx.Task()
            write_data_digital = [None for _ in range(len(digital_outputs))]
            for channel, value in digital_outputs.iteritems():
                output_task_digital.do_channels.add_do_chan(self.name+"/line"+str(channel))
                write_data_digital[i]=value
                i=i+1
            if clock_name == 'do':
                output_task_digital.timing.cfg_samp_clk_timing(1. / dt, source=None, samps_per_chan=nsamples)
            else:
                output_task_digital.timing.cfg_samp_clk_timing(1./dt, source=clock, samps_per_chan = nsamples)
            if i == 1:
                output_task_digital.write(write_data_digital[0]) #, timeout = nidaqmx.constants.WAIT_INFINITELY
            else:
                output_task_digital.write(write_data_digital) #, timeout = nidaqmx.constants.WAIT_INFINITELY


        if len(analog_outputs)>0:
            output_task.start()
        if len(digital_outputs)>0:
            output_task_digital.start()

        if len(analog_inputs)>0:
            input_task.start()
            data = input_task.read(number_of_samples_per_channel = nsamples)
        if len(digital_inputs)>0:
            input_task_digital.start()
            data_digital = input_task_digital.read(number_of_samples_per_channel = nsamples)

        if len(analog_inputs)>0:
            input_task.stop()
        if len(digital_inputs)>0:
            input_task_digital.stop()
        if len(analog_outputs)>0:
            output_task.stop()
        if len(digital_outputs)>0:
            output_task_digital.stop()

        # if len(analog_inputs) == 1: # maybe len(data) instead?
        #    data = [array(data)]
        #else:
        #    for i in range(len(analog_inputs)):
        #        data[i] = array(data[i])
        n = len(analog_inputs)
        if n == 0:
            data = []
        elif n == 1: # maybe len(data) instead?
            data = [array(data)]
        else:
            for i in range(n):
                data[i] = array(data[i])

        n = len(digital_inputs)
        if n == 0:
            data_digital = []
        elif n == 1: # maybe len(data) instead?
            data_digital = [array(data)]
        else:
            for i in range(n):
                data_digital[i] = array(data_digital[i])

        data= data+data_digital

        if len(analog_inputs)>0:
            input_task.close()
        if len(digital_inputs)>0:
            input_task_digital.close()
        if len(analog_outputs)>0:
            output_task.close()
        if len(digital_outputs)>0:
            output_task_digital.close()

        return data


if __name__ == '__main__':
    # print "Initializing"
    #from brian2 import volt, mV, nA, ms, pA, amp, second, zeros # for units
    ms = 0.001
    pA = 1e-12
    mV = 0.001
    volt = 1
    nA = 1e-9
    dt = 0.1*ms
    # print "Done"
    from pylab import *

    board = NI()
    board.sampling_rate = float(1./dt)

    ## These are not the correct gains (those of Axoclamp 2B)
    board.set_analog_input('Im', channel = 1, gain = 2.5*volt/nA)
    board.set_analog_input('Vm', channel = 0, gain = 10*mV/mV)
    #board.set_analog_input('Im2', channel = 2, gain = 1*volt/nA)
    #board.set_analog_input('V2', channel = 3, gain = 1)
    board.set_analog_output('Vc', channel = 0, gain= 50*mV/mV)
    board.set_analog_output('Ic', channel = 0, gain = 2.5*volt/nA)

    Ic = zeros(int(1000*ms/dt))
    Ic[int(130*ms/dt):int(330*ms/dt)] += 500*pA

    Vm, Im = board.acquire('Vm','Im', Ic = Ic)
    #Vm = board.acquire('Vm', Ic = Ic)

    del board

    R = (Vm[len(Vm)/2] - Vm[0])/(500*pA)
    print( R / 1e6)

    subplot(211)
    plot(array(Vm)/(mV))
    subplot(212)
    plot(Im/pA)
    show()

