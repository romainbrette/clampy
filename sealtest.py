'''
Seal test program in current clamp, with target voltages.
'''
from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation
from Tkinter import *

window = Tk()

board = DigiData()

scaling_factor =10./32767*array([1./0.1, # in nA
                                 1/0.01, # in mV
                                 1, # in nA
                                 1./0.01, # in mV
                                 1000.]) # in mV

#scaling_out = 32767/10.*1/0.02

Vm_text = StringVar()
Label(window, textvariable = Vm_text).pack()
I_text = StringVar()
Label(window, textvariable = I_text).pack()
R_text = StringVar()
Label(window, textvariable = R_text).pack()

#board.PutAOValue(1, x)

def refresh():
    Vm_text.set('Vm = '+board.GetAIValue(1) * scaling_factor[1]+'mV')
    I_text.set('I = '+board.GetAIValue(0) * scaling_factor[0]+'nA')
    window.after(200, refresh)

window.after(200, refresh)

mainloop()
