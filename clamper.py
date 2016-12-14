## CHECK THIS: https://searchcode.com/codesearch/view/27073964/

from Digidata1322A import *
from pylab import *
from time import sleep
import matplotlib.animation as animation

#board = DigiData()
#for i in range(100):
#    print board.GetAIValue(0)
#print board.hDev

ifo = DD132X_Info()
pnError = c_int() # error pointer
nDevs = DD132X_FindDevices(byref(ifo), 1, byref(pnError)) # should be at least 1
print nDevs,"device(s) found"

hDev = DD132X_OpenDevice(ifo.byAdaptor, ifo.byTarget, byref(pnError))

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
nsamples = 1000 # change
protocol = DD132X_Protocol()
protocol.dSampleInterval = 50. # 20 kHz
protocol.uLength = sizeof(protocol)
protocol.dwFlags = 0
protocol.uAIChannels = 1
protocol.anAIChannels[0] = 0
#protocol.anAIChannels[1] = 1
# Allocate data buffers
hostbuffer = (UINT*nsamples) ()
buffer = DATABUFFER()
buffer.uNumSamples = nsamples
buffer.uFlags = 0
buffer.pnData = byref(hostbuffer)
buffer.psDataFlags = None
buffer.pNextBuffer = byref(buffer)
buffer.pPrevBuffer = byref(buffer)

#buffer = [DATABUFFER() for i in range(protocol.uAIChannels)]
#for i in range(protocol.uAIChannels): # not clear: in fact maybe just 256 points buffers
#    buffer.uNumSamples = nsamples
#    buffer.uFlags = 0
#    buffer.pnData = byref(host) + i*nsamples*2
#    buffer.psDataFlags = None
#    buffer.pNextBuffer = buffer + ((i+1)*DATABUFFER.__sizeof__() % (2*DATABUFFER.__sizeof__()))
#    buffer.pPrevBuffer = buffer + ((i-1)*DATABUFFER.__sizeof__() % (2*DATABUFFER.__sizeof__()))
protocol.pAIBuffers = byref(buffer)
protocol.uAIBuffers = 1
protocol.uChunksPerSecond = 20 # no idea what this is
protocol.uTerminalCount = nsamples

# Start acquisition
DD132X_SetProtocol(hDev, byref(protocol), byref(pnError))
DD132X_StartAcquisition(hDev, byref(pnError))

#print DD132X_IsAcquiring(hDev)

# Check the progress of acquisition
'''
p = LONGLONG()
for i in range(20):
    DD132X_GetAcquisitionPosition(hDev, byref(p), byref(pnError))
    print p,pnError
    sleep(0.1)
'''

# Stop acquisition
sleep(1.)
DD132X_StopAcquisition(hDev, byref(pnError))
print hostbuffer

DD132X_CloseDevice(hDev, byref(pnError))
