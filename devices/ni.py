'''
National instruments board

There are a number of default values that we might need to look into.

Check this:
http://www.ni.com/tutorial/5409/en/
https://github.com/ni/nidaqmx-python/
'''
from board import *
import nidaqmx

class NI(Board):
    def __init__(self):
        Board.__init__(self)

    def acquire(self, inputs, outputs, dt):
        '''
        Acquires signals with sampling interval dt.

        Parameters
        ----------
        inputs : list of input names
        outputs : dictionary of output signals (key = output channel name, value = array with units)
        dt : sampling interval

        Returns a list of data arrays
        '''
        # Check that all output arrays have the same length
        nsamples = [len(output) for output in outputs.values()]
        if not all([nsample==nsamples[0] for nsample in nsamples]):
            raise Exception('Output arrays have different lengths.')
        nsamples = nsamples[0]

        # Read task
        input_task = nidaqmx.Task()
        for name in inputs:
            input_task.ai_channels.add_ai_voltage_chan("Dev1/ai"+str(self.analog_input[name]), name_to_assign_to_channel = name)
        input_task.timing.cfg_samp_clk_timing(1./dt, source="/Dev1/ao/SampleClock", samps_per_chan = nsamples)

        # Write task
        output_task = nidaqmx.Task()
        write_data = []
        for name, value in outputs.iteritems():
            output_task.ao_channels.add_ai_voltage_chan("Dev1/ao"+str(self.analog_output[name]), name_to_assign_to_channel = name)
            write_data.append(value)
        output_task.timing.cfg_samp_clk_timing(1./dt, source=None, samps_per_chan = nsamples)

        output_task.write(write_data) #, timeout = nidaqmx.constants.WAIT_INFINITELY

        input_task.start()
        output_task.start()

        data = input_task.read()

        input_task.stop()
        output_task.stop()

        return data


if __name__ == '__main__':
    from brian2 import volt, mV, nA, ms, pA, zeros # for units
    from pylab import *

    board = NI()
    ## These are not the correct gains (those of Axoclamp 2B)
    board.set_analog_input('Im', channel = 0, gain = 0.1*volt/nA)
    board.set_analog_input('Vm', channel = 1, gain = 10*mV/mV)
    #board.set_analog_input('Im2', channel = 2, gain = 1*volt/nA)
    #board.set_analog_input('V2', channel = 3, gain = 1)
    board.set_analog_output('Vc', channel = 0, gain= 0.02*volt/volt)
    board.set_analog_output('Ic', channel = 0, gain = 1*nA/volt)

    dt = 0.1*ms
    Ic = ones(int(300*ms/dt))*10*pA
    Ic[int(30*ms/dt):int(230*ms/dt)] += 500*pA

    Vm, = board.acquire(('Vm',), {'Ic' : Ic}, dt = dt)

    del board

    plot(Vm/mV)
    show()





''' # From ACQ4
task1 = n.createTask()
task1.CreateAIVoltageChan("/Dev1/ai0", "", n.Val_RSE, -10., 10., n.Val_Volts, None)
task1.CfgSampClkTiming("/Dev1/ao/SampleClock", 10000.0, n.Val_Rising, n.Val_FiniteSamps, 100)

task2 = n.createTask()
task2.CreateAOVoltageChan("/Dev1/ao0", "", -10., 10., n.Val_Volts, None)
# task2.CfgSampClkTiming(None, 10000.0, nidaq.Val_Rising, nidaq.Val_FiniteSamps, 1000)
task2.CfgSampClkTiming(None, 10000.0, n.Val_Rising, n.Val_FiniteSamps, 100)
# task2.CfgDigEdgeStartTrig("ai/StartTrigger", nidaq.Val_Rising)



data1 = np.zeros((100,), dtype=np.float64)
data1[20:40] = 7.0
data1[60:80] = 5.0
print "  Wrote ao samples:", task2.write(data1)
task1.start()
task2.start()

data2 = task1.read()
# time.sleep(1.0)
task1.stop()
task2.stop()

print "  Data acquired:", data2[0].shape
return data2
'''