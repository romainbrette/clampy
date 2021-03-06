'''
A simple voltage clamp script.
This one does experiment and analysis in the same script.
'''

from clampy import *
from pylab import *
from clampy.brianmodels import *
from clampy.data_management import *
from clampy.signals import *
import os
import shutil

from init_rig import *

do_experiment = not os.path.exists('Steps')

# Parameters
ntrials = 10

if do_experiment:
    # Make a data folder
    if not os.path.exists('data'):
        os.mkdir('data')
    path = 'data/'+date_time()+' Voltage clamp'
    os.mkdir(path)
    # Saving current script
    shutil.copy(__file__, path)

    # Experiment
    os.mkdir(path+'/Steps')
    I = []
    for ampli in linspace(-100,20,ntrials)*mV:
        print('Amplitude: {}'.format(str(ampli)))
        Vc = sequence([constant(10*ms, dt)*0*mV,
                       constant(60*ms, dt)*ampli,
                       constant(130*ms, dt)*0*mV])
        I.append(board.acquire('I', V=Vc))

    # Save data
    savetxt(path+'/Steps/I.txt',I)
    savetxt(path+'/Steps/V.txt',Vc)

    # Save parameter values
    save_info(dict(amplitude=float(ampli), duration=len(Vc)*float(dt), dt=float(dt)),
              path+'/voltage_clamp_experiment.info')
else: # Loading the data after the experiment
    from clampy.setup.units import *
    path = '.'
    I = loadtxt(path+'/Steps/I.txt')*amp
    Vc = loadtxt(path + '/Steps/V.txt')*volt

# Plotting
figure()
t = dt*arange(len(Vc))
for Ii in I:
    plot(t/ms, array(Ii) / nA)
xlabel('Time (ms)')
ylabel('Current (nA)')
title('Response to voltage pulses')

show()
