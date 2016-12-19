## CHECK THIS: https://searchcode.com/codesearch/view/27073964/

from Digidata1322A import *
from pylab import *
from time import sleep
import matplotlib.animation as animation
from ctypes import cast

#board = DigiData()
#for i in range(100):
#    print board.GetAIValue(0)
#print board.hDev

ifo = DD132X_Info()

pnError = c_int() # error pointer
nDevs = DD132X_FindDevices(byref(ifo), 1, byref(pnError)) # should be at least 1
print nDevs,"device(s) found"

hDev = DD132X_OpenDevice(ifo.byAdaptor, ifo.byTarget, byref(pnError))
print ifo.uInputBufferSize, ifo.uOutputBufferSize, ifo.uLength


protocol = DD132X_Protocol()
#DD132X_GetProtocol(hDev, byref(protocol), byref(pnError))
#print protocol,pnError
#print protocol.uLength, protocol.dSampleInterval, protocol.uAIChannels, protocol.uAOChannels
"""
DD132X_Protocol._fields_ = [
    ('uLength', UINT),                              # Size of this structure in bytes
    ('dSampleInterval', c_double),                  # Sample interval in us; 500 kHz / number of input channels
    ('dwFlags', DWORD),                             # Boolean flags that control options. (0)
    ('eTriggering', DD132X_Triggering),             # probably DD132X_StartImmediately
    ('eAIDataBits', DD132X_AIDataBits),             # probably DD132X_Bit0Data
    ('uAIChannels', UINT),                          # number of input channels
    ('anAIChannels', c_int * 64),                   # 64 = "scanlist_size" : list of channel indexes
    ('pAIBuffers', POINTER(DATABUFFER)),            # circular chained list of buffers
    ('uAIBuffers', UINT),                           # number of buffers?
    ('uAOChannels', UINT),                          # id. for output channels
    ('anAOChannels', c_int * 64),
    ('pAOBuffers', POINTER(DATABUFFER)),
    ('uAOBuffers', UINT),
    ('uTerminalCount', LONGLONG),                   # ?? probably not needed
    ('eOutputPulseType', DD132X_OutputPulseType),   # probably DD132X_NoOutputPulse
    ('bOutputPulsePolarity', c_short),              # n/a
    ('nOutputPulseChannel', c_short),               # n/a
    ('wOutputPulseThreshold', WORD),                # n/a
    ('wOutputPulseHystDelta', WORD),                # n/a
    ('uChunksPerSecond', UINT),                     # Granularity of data transfer
    ('byUnused', BYTE * 248),
]
"""
#### CHECK Axon's files; the .h file has a little more info
# https://searchcode.com/codesearch/view/27073964/

# Make an acquisition protocol
nsamples = 256
protocol = DD132X_Protocol()
protocol.dSampleInterval = c_double(20.) # 20 kHz
protocol.dwFlags = 0
protocol.eTriggering = DD132X_StartImmediately
protocol.eAIDataBits = 0#DD132X_Bit0Data
protocol.uAIChannels = 1
protocol.anAIChannels[0] = 0
protocol.uAOChannels = 0
protocol.uOutputPulseType = DD132X_NoOutputPulse
#protocol.anAIChannels[1] = 1
# Allocate data buffers
hostbuffer = (ADC_VALUE*nsamples) ()

print array(hostbuffer)[:100]

buffer = DATABUFFER()
buffer.uNumSamples = nsamples
buffer.uFlags = 0
buffer.pnData = hostbuffer
buffer.psDataFlags = None
buffer.pNextBuffer = pointer(buffer)
buffer.pPrevBuffer = pointer(buffer)

#buffer = [DATABUFFER() for i in range(protocol.uAIChannels)]
#for i in range(protocol.uAIChannels): # not clear: in fact maybe just 256 points buffers
#    buffer.uNumSamples = nsamples
#    buffer.uFlags = 0
#    buffer.pnData = byref(host) + i*nsamples*2
#    buffer.psDataFlags = None
#    buffer.pNextBuffer = buffer + ((i+1)*DATABUFFER.__sizeof__() % (2*DATABUFFER.__sizeof__()))
#    buffer.pPrevBuffer = buffer + ((i-1)*DATABUFFER.__sizeof__() % (2*DATABUFFER.__sizeof__()))
protocol.pAIBuffers = pointer(buffer)
protocol.uAIBuffers = 1
#protocol.uChunksPerSecond = 20 # no idea what this is
protocol.uTerminalCount = LONGLONG(nsamples)
#protocol.uLength = sizeof(protocol)

# Start acquisition
DD132X_SetProtocol(hDev, byref(protocol), byref(pnError))
DD132X_StartAcquisition(hDev, byref(pnError))

print pnError

# Stop acquisition
sleep(1)

n = LONGLONG()

'''
for _ in range(100):
    sleep(0.05)
    DD132X_GetAcquisitionPosition(hDev, byref(n), byref(pnError))
    print n
'''

DD132X_GetAcquisitionPosition(hDev, byref(n), byref(pnError))
print n

DD132X_StopAcquisition(hDev, byref(pnError))
print pnError

print array(hostbuffer)[:100]

DD132X_CloseDevice(hDev, byref(pnError))
