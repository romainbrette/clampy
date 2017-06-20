'''
National instruments board

Check this:
http://www.ni.com/tutorial/5409/en/
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
        '''
        # Check that all output arrays have the same length
        nsamples = [len(output) for output in outputs.values()]
        if not all([nsample==nsamples[0] for nsample in nsamples]):
            raise Exception('Output arrays have different lengths.')
        nsamples = nsamples[0]

        task1 = nidaqmx.Task()
        task1.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        task1.timing.cfg_samp_clk_timing(1./dt, source="/Dev1/ao/SampleClock", samps_per_chan = nsamples)
        #data = task1.read(number_of_samples_per_channel=nsamples)

        task2 = nidaqmx.Task()
        task2.ao_channels.add_ai_voltage_chan("Dev1/ao0")
        task2.timing.cfg_samp_clk_timing(1./dt, source=None, samps_per_chan = nsamples)

        return data


if __name__ == '__main__':
    ni = NI()
    print ni.acquire(None, None, None)

'''
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