"""
Demonstrates the use of the Multiclamp 700B
"""
from clampy import *
from pylab import *
from clampy.signals import *
from init_rig import *

amplifier.set_bridge_balance(True)
Rs = amplifier.auto_bridge_balance()
print "Bridge resistance:", Rs / 1e6
