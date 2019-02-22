'''
These are models of RC circuits.
'''
from brian2 import *
from .brianmodels import *

__all__ = ['RC','RC_and_electrode']

class RC(BrianExperiment):
    '''
    An RC model with parameters similar to Paramecium passive properties.
    These are based on properties of P. Caudatum, larger than P. Tetraurelia

    R = 65 MOhm
    C = 700 pF
    V0 = -30 mV
    '''
    def __init__(self, R = 65*Mohm, C = 700*pF, V0 = -30*mV, dt = 0.1*ms, gclamp = 10*usiemens):
        eqs = 'dV/dt = (I-(V-V0)/R)/C : volt'

        namespace = dict(R=R, C=C, V0=V0)

        BrianExperiment.__init__(self,eqs,namespace,gclamp,dt)

        self.neuron.V = V0

class RC_and_electrode(BrianExperiment):
    '''
    A model consisting of an RC cell together with an electrode model.

    The electrode is 50 MOhm, time constant of 0.5 ms (by default).
    '''
    def __init__(self, R = 65*Mohm, C = 700*pF, V0 = -30*mV, Re = 50*Mohm, Ce = 10*pF,
                 dt = 0.1*ms, gclamp = 10*usiemens):
        eqs = '''
        dVm/dt = (Ie-(Vm-V0)/R)/C : volt
        dV/dt = (I-Ie)/Ce : volt
        Ie = (V-Vm)/Re : amp
        V2 = Vm : volt
        '''

        namespace = dict(R=R, C=C, V0=V0, Re=Re, Ce=Ce)

        BrianExperiment.__init__(self,eqs,namespace,gclamp,dt)

        self.neuron.V = V0
        self.neuron.Vm = V0
