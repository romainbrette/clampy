from pylab import *
from os.path import join
from clampy.data_management import load_dataset

ms = 0.001
dt = 0.025*ms

data_path = 'tuning'

M = load_dataset(join(data_path, 'data'))
ind = M['t']<50*ms
print(M['V2'].shape)

C = arange(M['V2'].shape[0])*.1
Cs = C[-1]
#loglog(Cs-C, [V[ind].var() for V in M['V2']])
#plot(C, [V[ind].var() for V in M['V2']])
plot(M['V2'][0]*1000,'r')
plot(M['V2'][42]*1000,'k')


show()
