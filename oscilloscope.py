from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation

ifo = DD132X_Info()
pnError = c_int() # error pointer
nDevs = DD132X_FindDevices(byref(ifo), 1, byref(pnError)) # should be at least 1
print nDevs,"device(s) found"

hDev = DD132X_OpenDevice(ifo.byAdaptor, ifo.byTarget, byref(pnError))

# Oscilloscope
sampling_f = 100.
oscillo_f = 1.
n = int(sampling_f/oscillo_f)
signal = zeros(n)
x = c_short()

fig=figure()
xlim(0,1)
DD132X_GetAIValue(hDev, 1, byref(x), byref(pnError))
z = x.value / 32767. # Note that we need to calibrate the signal
ylim(z*.99,z*1.01)
t=linspace(0,1,n)
line, = plot(t,signal)

t1 = time()
for _ in range(100):
    DD132X_GetAIValue(hDev, 1, byref(x), byref(pnError))
t2 = time()
print "Mean latency:",(t2-t1)*10,"ms"

def update(i):
    t0=time()
    for i in range(n):
        DD132X_GetAIValue(hDev, 1, byref(x), byref(pnError))
        signal[i] = x.value / 32767.
        t=time()
        if (t-t0<i/sampling_f): # latency is already pretty bad
            sleep(i/sampling_f-t+t0)
    line.set_ydata(signal)
    return line,

anim = animation.FuncAnimation(fig,update,interval = 1./oscillo_f)

show()


DD132X_CloseDevice(hDev, byref(pnError))
