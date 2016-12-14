'''
Resistance measurement with the Digidata, using direct access
'''

from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation

board = DigiData()
#for i in range(100):
#    print board.GetAIValue(0)
#print board.hDev
for _ in range(20):
    print time(),[board.GetAIValue(i) for i in range(12)]
# calibration?

print

board.PutAOValue(1, 10000) # sets the command; the command remains
for _ in range(20):
    print time(),[board.GetAIValue(i) for i in range(12)]

print

board.PutAOValue(1, 0)
sleep(0.2) # there seems to be a 200 ms transient in the response (measured I??)
for _ in range(20):
    print time(),[board.GetAIValue(i) for i in range(12)]
