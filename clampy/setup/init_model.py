'''
Initializes for model running mode.
'''
from brian2 import *
from clampy.brianmodels import *

dt = 0.1*ms
board = RC_and_electrode(Ce = 3*pF)
amplifier = board
board.set_aliases(Ic1='Ic', V1='V', V2='V', I_TEVC='Ic')
