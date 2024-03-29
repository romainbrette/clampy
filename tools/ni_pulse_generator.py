'''
A GUI to generate periodic pulses on a NI board.

# Sets counter 0 to PFI1
board.connect_counter_to_PFI(0, 1)
'''
from clampy import *
from init_rig import *
import tkinter as tk

window = tk.Tk()
window.title('NI pulse generator')

text_channel = tk.Label(text="Channel")
text_channel.pack()
entry_channel = tk.Entry()
entry_channel.insert(0, '0')
entry_channel.pack()

text_freq = tk.Label(text="Frequency (Hz)")
text_freq.pack()
entry_freq = tk.Entry()
entry_freq.insert(0, '25')
entry_freq.pack()

text_dur = tk.Label(text="Duration (ms)")
text_dur.pack()
entry_dur = tk.Entry()
entry_dur.insert(0, '1')
entry_dur.pack()

task = None

def command_start():
    global task
    channel = int(entry_channel.get())
    freq = float(entry_freq.get())
    duration = float(entry_dur.get())*.001
    task = board.start_pulses(channel, freq, freq*duration)

def command_stop():
    task.stop()
    task.close()

button_start = tk.Button(text="Start", command=command_start)
button_start.pack()
button_stop = tk.Button(text="Stop", command=command_stop)
button_stop.pack()

window.mainloop()
