'''
Resistance measurement with the Digidata, using direct access
'''

from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation
from Tkinter import *

window = Tk()

board = DigiData()

"""
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
"""

scaling_factor =10./32767*array([1./0.1, # in nA
                                 1/0.01, # in mV
                                 1, # in nA
                                 1./0.01, # in mV
                                 1000.]) # in mV

scale=[]
for _ in range(5):
    s = Scale(window, orient=HORIZONTAL, from_=-1000, to=1000)
    s.pack()
    scale.append(s)

x = 0
def press():
    global x
    x = 10000 - x
    board.PutAOValue(1, x)

Button(window, text = 'Inject', command = press).pack()

def refresh():
    for i in range(5):
        scale[i].set(board.GetAIValue(i) * scaling_factor[i])
    window.after(200, refresh)

window.after(200, refresh)

mainloop()
