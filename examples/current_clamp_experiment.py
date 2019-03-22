'''
A simple current clamp script.
This one does analysis in a separate script, which it calls at the end.
'''

from clampy import *
from pylab import *
from clampy.brianmodels import *
import os
import shutil
from current_clamp_analysis import *

from init_rig import *

# Parameters
ntrials = 10

# Make a data folder
if not os.path.exists('data'):
    os.mkdir('data')
path = 'data/'+date_time()+' Current clamp'
os.mkdir(path)
# Copy current script and analysis script
shutil.copy('current_clamp_experiment.py',path)
shutil.copy('current_clamp_analysis.py',path)

# Experiment
os.mkdir(path+'/Steps')
V = []
for ampli in linspace(-1,1,ntrials)*nA:
    print 'Amplitude ',ampli
    Ic = sequence([constant(10*ms, dt)*0*amp,
                   constant(60*ms, dt)*ampli,
                   constant(130*ms, dt)*0*amp])
    V.append(board.acquire('V', Ic=Ic))

# Save data
savetxt(path+'/Steps/I.txt',Ic)
savetxt(path+'/Steps/V.txt',V)

# Save parameter values
save_info(dict(amplitude=float(ampli), duration=len(Ic)*float(dt), dt=float(dt)),
          path+'/current_clamp_experiment.info')

# Plot
do_analysis(path)
