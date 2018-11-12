'''
Seal test program in current clamp, with target voltages.

IN PROGRESS
'''
from Digidata1322A import *
from pylab import *
from time import sleep, time
import matplotlib.animation as animation
from Tkinter import *

Vcommand = -60 # mV

window = Tk()

board = DigiData()

scaling_factor =10./32767*array([1./0.1, # in nA
                                 1/0.01, # in mV
                                 1, # in nA
                                 1./0.01, # in mV
                                 1000.]) # in mV

scaling_out = 32767/10. # nA

Vm_text = StringVar()
Label(window, textvariable = Vm_text).pack()
I_text = StringVar()
Label(window, textvariable = I_text).pack()
R_text = StringVar()
Label(window, textvariable = R_text).pack()

on = False
Vm = board.GetAIValue(1)* scaling_factor[1]
previousVm = Vm+10

def refresh():
    global on, Vm, Im, I, R
    previousVm = Vm
    Vm = board.GetAIValue(1)* scaling_factor[1]
    Vm_text.set('Vm = '+ str(Vm)+'mV')
    I_text.set('I = '+str(I)+'nA')
    if on:
        I = (Vcommand-Vm)/R
        board.PutAOValue(1, I*scaling_out)
    else:
        board.PutAOValue(1, 0)
        # Calculate resistance
        R = (previousVm-Vm)/I
    on = not on
    window.after(20, refresh)

window.after(20, refresh)

mainloop()
