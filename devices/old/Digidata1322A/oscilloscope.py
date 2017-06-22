from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation

# Oscilloscope
sampling_f = 10000.
oscillo_f = 100.
duration = 1.
nsamples = int(duration*sampling_f)

# Ampli
ifo = DD132X_Info()
pnError = c_int() # error pointer
nDevs = DD132X_FindDevices(byref(ifo), 1, byref(pnError)) # should be at least 1
print nDevs,"device(s) found"

hDev = DD132X_OpenDevice(ifo.byAdaptor, ifo.byTarget, byref(pnError))

protocol = DD132X_Protocol()

# Make an acquisition protocol
protocol = DD132X_Protocol()
protocol.dSampleInterval = c_double(float64(1e6/sampling_f))
protocol.dwFlags = 0 #0
protocol.eTriggering = DD132X_StartImmediately
protocol.eAIDataBits = 0#DD132X_Bit0Data
protocol.uAIChannels = 1
protocol.anAIChannels[0] = 1
protocol.uAOChannels = 0
protocol.uOutputPulseType = DD132X_NoOutputPulse
# Allocate data buffers
protocol.pAIBuffers = None
protocol.uAIBuffers = 0 #1
protocol.uChunksPerSecond = 20 # no idea what this is
#protocol.uTerminalCount = LONGLONG(nsamples)
#protocol.uLength = sizeof(protocol)

# Start acquisition
DD132X_SetProtocol(hDev, byref(protocol), byref(pnError))
DD132X_StartReadLast(hDev, byref(pnError))

#nsamples = int(sampling_f/oscillo_f)
signal = (ADC_VALUE*nsamples) ()

fig=figure()
xlim(0,1)
ylim(-32767,32768)
t=linspace(0,1,nsamples)
line, = plot(t,array(signal))

def update(i):
    DD132X_ReadLast(hDev, signal, nsamples, byref(pnError))
    line.set_ydata(array(signal))
    return line,

anim = animation.FuncAnimation(fig,update,interval = 1./oscillo_f)

show()

DD132X_StopAcquisition(hDev, byref(pnError))
DD132X_CloseDevice(hDev, byref(pnError))
