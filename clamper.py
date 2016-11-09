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
DD132X_GetProtocol(hDev, byref(protocol), byref(pnError))
print protocol,pnError
print protocol.uLength, protocol.dSampleInterval, protocol.uAIChannels, protocol.uAOChannels
"""
DD132X_Protocol._fields_ = [
    ('uLength', UINT),
    ('dSampleInterval', c_double),
    ('dwFlags', DWORD),
    ('eTriggering', DD132X_Triggering),
    ('eAIDataBits', DD132X_AIDataBits),
    ('uAIChannels', UINT),
    ('anAIChannels', c_int * 64),
    ('pAIBuffers', POINTER(DATABUFFER)),
    ('uAIBuffers', UINT),
    ('uAOChannels', UINT),
    ('anAOChannels', c_int * 64),
    ('pAOBuffers', POINTER(DATABUFFER)),
    ('uAOBuffers', UINT),
    ('uTerminalCount', LONGLONG),
    ('eOutputPulseType', DD132X_OutputPulseType),
    ('bOutputPulsePolarity', c_short),
    ('nOutputPulseChannel', c_short),
    ('wOutputPulseThreshold', WORD),
    ('wOutputPulseHystDelta', WORD),
    ('uChunksPerSecond', UINT),
    ('byUnused', BYTE * 248),
]
"""

#protocol = DD132X_Protocol()

# Start acquisition
#DD132X_StartAcquisition(hDev, byref(pnError))

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
#DD132X_StopAcquisition(hDev, byref(pnError))


DD132X_CloseDevice(hDev, byref(pnError))
