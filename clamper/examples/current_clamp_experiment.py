'''
A simple current clamp script.
'''

from clamper import *
from pylab import *
from clamper.brianmodels import *
from clamper.data_management import *
from clamper.signals import *
import os

from init_rig import *

# Don't do the experiment if there is data in this folder
do_experiment = not os.path.exists('Steps')

# Parameters
ntrials = 10

if do_experiment:
    # Make a data folder
    if not os.path.exists('data'):
        os.mkdir('data')
    path = 'data/'+date_time()+' Current clamp'
    os.mkdir(path)
    # Saving current script
    save_current_script(path+'/current_clamp_experiment.py')

    # Experiment
    os.mkdir(path+'/Steps')
    V = []
    for ampli in linspace(-1,1,ntrials)*nA:
        print 'Amplitude ',ampli
        Ic = sequence([constant(10*ms, dt)*0*amp,
                       constant(60*ms, dt)*ampli,
                       constant(130*ms, dt)*0*amp])
        V.append(amplifier.acquire('V', I=Ic))

    # Save data
    savetxt(path+'/Steps/I.txt',array(Ic)/nA)
    savetxt(path+'/Steps/V.txt',array(V)/mV)

    # Save parameter values
    save_info(dict(amplitude=ampli/nA, duration=len(Ic)*dt/ms, dt=dt/ms),
              path+'/current_clamp_experiment.info')
else: # Loading the data after the experiment
    from clamper.setup.units import *
    path = '.'
    Ic = loadtxt(path+'/Steps/I.txt')*nA
    V = loadtxt(path + '/Steps/V.txt')*mV

# Plotting
figure()
t = dt*arange(len(Ic))
for Vi in V:
    plot(t/ms, array(Vi) / mV)
xlabel('Time (ms)')
ylabel('Voltage (mV)')
title('Response to current pulses')

show()
