'''
A simple voltage clamp script.
'''

from clamper import *
from pylab import *
from clamper.brianmodels import *
from clamper.data_management import *
from clamper.signals import *
import os

from init_rig import *

# If do_experiment is not set, then set it to True
try:
    do_experiment
except NameError:
    do_experiment = True

# Parameters
ntrials = 10

if do_experiment:
    # Make a data folder
    if not os.path.exists('data'):
        os.mkdir('data')
    path = 'data/'+date_time()+' Voltage clamp'
    os.mkdir(path)
    # Saving current script
    save_current_script(path+'/voltage_clamp_experiment.py')

    # Experiment
    os.mkdir(path+'/Steps')
    I = []
    for ampli in linspace(-100,20,ntrials)*mV:
        print 'Amplitude ',ampli
        Vc = sequence([constant(10*ms, dt)*0*mV,
                       constant(60*ms, dt)*ampli,
                       constant(130*ms, dt)*0*mV])
        I.append(amplifier.acquire('I', V=Vc))

    # Save data
    savetxt(path+'/Steps/I.txt',array(I)/nA)
    savetxt(path+'/Steps/V.txt',array(Vc)/mV)

    # Save parameter values
    save_info(dict(amplitude=ampli/mV, duration=len(Vc)*dt/ms, dt=dt/ms),
              path+'/voltage_clamp_experiment.info')
else: # Loading the data after the experiment
    from clamper.setup.units import *
    path = '.'
    I = loadtxt(path+'/Steps/I.txt')*nA
    Vc = loadtxt(path + '/Steps/V.txt')*mV

# Plotting
figure()
t = dt*arange(len(Vc))
for Ii in I:
    plot(t/ms, array(Ii) / nA)
xlabel('Time (ms)')
ylabel('Current (nA)')
title('Response to voltage pulses')

show()
