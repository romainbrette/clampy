'''
Initializes for model running mode.
'''
from brian2 import *
from clamper.brianmodels import *

dt = 0.1*ms
board = RC_and_electrode(Ce = 3*pF)
amplifier = board
