# coding: utf-8
'''
Brian models that can be run as if they were an acquisition board
'''

__all__ = ['BrianExperiment', 'TwoCompartmentModel', 'SpatialBrianExperiment', 'AxonalInitiationModel']

from brian2 import *
from clampy.devices import Board

class BrianExperiment(Board):
    '''
    A neuron model that can be recorded in current-clamp or voltage-clamp.

    The equations must include V (membrane potential) and I (injected current).
    '''
    def __init__(self, eqs = None, namespace = None, gclamp = 10*usiemens, dt = 0.1*ms, method='exponential_euler'):
        '''
        Parameters
        ----------
        eqs : Brian equations of the model
        namespace : namespace of the model
        gclamp : gain of the voltage-clamp
        dt : sampling step (not the same as the simulation time step)
        '''
        Board.__init__(self)
        self.alias = dict() # dictionary of aliases (mapping from alias to channel name)
        self.eqs = Equations(eqs+'''
        I = Icommand(t-t_start) + Iclamp : amp
        Iclamp = gclamp*(Vcommand(t-t_start)-V) : amp
        gclamp : siemens
        t_start : second
        ''')
        self.dt = dt
        self.sampling_rate = 1./dt
        self.gclamp = gclamp
        self.neuron = NeuronGroup(1, self.eqs, namespace=namespace, method=method)
        self.network = Network(self.neuron)

        self.configure_board()
        self.is_voltage_clamp = False # Initially in current clamp

    def configure_board(self):
        # Expose all variables
        for name in self.eqs.eq_names:
            self.set_analog_input(name, name, gain=1.)
        self.set_analog_output('Vc', 'Vc', gain=1.)
        self.set_analog_output('Ic', 'Ic', gain=1.)

    def current_clamp(self, channel=None):
        self.is_voltage_clamp = False

    def voltage_clamp(self, channel=None):
        self.is_voltage_clamp = True

    def acquire_raw(self, analog_inputs=None, analog_outputs=None, digital_inputs=None, digital_outputs=None, input_range={}):
        '''
        Send commands and acquire signals.

        Parameters
        ----------
        analog_inputs
            A list of input variables to acquire. From: V, I, Ve (electrode potential)
            A maximum of two inputs.
        analog_outputs
            A dictionary of commands.
        '''
        if analog_outputs != {}: # We might to do a more thorough checking
            nsamples = len(list(analog_outputs.values())[0])
        else:
            nsamples = len(list(digital_outputs.values())[0])

        self.neuron.t_start = self.network.t
        if 'Vc' in analog_outputs:
            Vcommand = TimedArray(analog_outputs['Vc'], dt=self.dt, name='Vclamp')
            if not 'Ic' in analog_outputs: # Automatic mode switch
                self.voltage_clamp()
        else:
            Vcommand = TimedArray([0 * volt], dt=self.dt, name='Vclamp')
        if 'Ic' in analog_outputs:
            Icommand = TimedArray(analog_outputs['Ic'], dt=self.dt, name='Iclamp')
            if not 'Vc' in analog_outputs:
                self.current_clamp()
        else:
            Icommand = TimedArray([0 * amp], dt=self.dt, name='Iclamp')

        self.neuron.gclamp[0] = self.gclamp * self.is_voltage_clamp

        self.monitor = StateMonitor(self.neuron, analog_inputs, record=[0], dt = self.dt)
        self.network.add(self.monitor)
        self.network.run(nsamples * self.dt)

        results = [self.monitor[0].__getattr__(name) for name in analog_inputs]

        self.network.remove(self.monitor)

        return results

class TwoCompartmentModel(BrianExperiment):
    '''
    A two compartment model with soma and AIS.

    From:
    Teleńczuk M, Fontaine B, Brette R (2017).
    The basis of sharp spike onset in standard biophysical models.
    PLoS ONE
    https://doi.org/10.1371/journal.pone.0175362
    '''
    def __init__(self, gclamp = 10*usiemens, dt = 0.1*ms):
        eqs = '''
            dvs/dt = (gL*(EL-vs) + INa_soma + IK_soma + Ia + I) /Cs : volt
            V = vs : volt
            dva/dt = (INa_axon + IK_axon - Ia) /Ca : volt
            Ia = (va-vs)/Ra : amp

            INa_axon = gNa_axon*(ENa-va)*m_axon*h_axon : amp
            dm_axon/dt = (1/(1+exp((v12-va)/ka))-m_axon)/taum : 1
            dh_axon/dt = (1/(1+exp((va-v12_inact)/ka))-h_axon)/tauh : 1

            INa_soma = gNa_soma*(ENa-vs)*m_soma*h_soma : amp
            dm_soma/dt = (1/(1+exp((v12-vs)/ka))-m_soma)/taum : 1
            dh_soma/dt = (1/(1+exp((va-v12_inact)/ka))-h_soma)/tauh : 1

            IK_axon = gK_axon*(EK-va)*n_axon : amp
            dn_axon/dt = (1/(1+exp((v12_K-va)/kn))-n_axon)/taun : 1

            IK_soma = gK_soma*(EK-vs)*n_soma : amp
            dn_soma/dt = (1/(1+exp((v12_K-vs)/kn))-n_soma)/taun : 1
        '''

        # Na channels
        ENa = 60 * mV
        v12 = -25 * mV
        ka = 6 * mV
        taum = 100 * us
        v12_inact = -35 * mV
        tauh = 0.5*ms

        # K channels
        EK = -90 * mV
        v12_K = -15 * mV
        kn = 4*mV
        taun = 2*ms

        # Somatic compartment
        Cs = 250 * pF
        EL = -80 * mV
        gL = 12*nS
        gNa_soma = 800*nS
        gK_soma = 2200*nS

        # Axonal compartment
        Ca = 5*pF
        gNa_axon = 1200*nS
        gK_axon = 1200*nS

        # Coupling
        Ra = 4.5*Mohm

        namespace = dict(ENa=ENa, v12=v12,ka=ka,taum=taum,v12_inact=v12_inact,
                         EK=EK,v12_K=v12_K,
                         Cs=Cs,EL=EL,gL=gL,gNa_soma=gNa_soma,gK_soma=gK_soma,
                         Ca=Ca,gNa_axon=gNa_axon,gK_axon=gK_axon,
                         Ra=Ra,
                         tauh=tauh,taun=taun,kn=kn)

        BrianExperiment.__init__(self,eqs,namespace,gclamp,dt)

        self.neuron.vs = EL
        self.neuron.va = EL
        self.neuron.h_soma = 1
        self.neuron.h_axon = 1

class TwoCompartmentModel2(BrianExperiment):
    '''
    A two compartment model with soma and AIS.
    '''
    def __init__(self, gclamp = 10*usiemens, dt = 0.1*ms):
        # Somatic compartment
        Cs = 250 * pF
        EL = -80 * mV
        gL = 12*nS
        gNa_soma = 500*nS
        gK_soma = 500*nS

        # Axonal compartment
        Ca = 5*pF
        gNa_axon = 1200*nS
        gK_axon = 600*nS

        # Coupling
        Ra = 4.5*Mohm

        ### AIS

        # Na channels parameters
        ENa = 70. * mV
        EK = -90. * mV

        ## Correction for temperature
        T = 33.
        factor = (1 / 2.8) ** ((T - 23.) / 10.)

        ## Channels kinetics at axon
        # Na+:
        Va = -35. * mV  # Schmidt-Heiber 2010, ~23°C
        Ka = 6. * mV  # Schmidt-Heiber 2010, ~23°C
        Taum_max = factor * 0.15 * ms  # Schmidt-Heiber 2010, ~23°C
        Vh = -67. * mV  # Schmidt-Heiber 2010, ~23°C
        Kh = 9. * mV  # Schmidt-Heiber 2010, ~23°C
        Tauh_max = factor * 10. * ms  # Schmidt-Heiber 2010, ~23°C

        # K+:
        Vn = -73. * mV  # n8 fit from Hallerman 2012
        Kn = 18. * mV  # n8 fit from Hallerman 2012
        Taun_max = 1.4 * ms  # n8 fit from Hallerman 2012

        ## Channels kinetics
        # Na+:
        Va_soma = -29 * mV  # Schmidt-Heiber 2010, ~23°C
        Ka_soma = 7. * mV  # Schmidt-Heiber 2010, ~23°C
        Taum_max_soma = factor * 0.2 * ms  # Schmidt-Heiber 2010, ~23°C
        Vh_soma = -59 * mV  # Schmidt-Heiber 2010, ~23°C
        Kh_soma = 11. * mV  # Schmidt-Heiber 2010, ~23°C
        Tauh_max_soma = factor * 11. * ms  # Schmidt-Heiber 2010, ~23°C

        # Equations
        eqs = '''
        dvs/dt = (gL*(EL-vs) + INa_soma + IK_soma + Ia + I) /Cs : volt
        V = vs : volt
        dva/dt = (INa_axon + IK_axon - Ia) /Ca : volt
        Ia = (va-vs)/Ra : amp

        INa_soma = gNa_soma*(ENa-vs)*m_soma*h_soma : amp
        INa_axon = gNa_axon*(ENa-va)*m_axon*h_axon : amp
        IK_soma = gK_soma*(EK-vs)*n_soma**8 : amp
        IK_axon = gK_axon*(EK-va)*n_axon**8 : amp

        dm_soma/dt = alpham_soma*(1-m_soma) - betam_soma*m_soma : 1
        dh_soma/dt = alphah_soma*(1-h_soma) - betah_soma*h_soma : 1
        dn_soma/dt = alphan_soma*(1-n_soma) - betan_soma*n_soma : 1
        dm_axon/dt = alpham_axon*(1-m_axon) - betam_axon*m_axon : 1
        dh_axon/dt = alphah_axon*(1-h_axon) - betah_axon*h_axon : 1
        dn_axon/dt = alphan_axon*(1-n_axon) - betan_axon*n_axon : 1

        alpham_axon = (1/Ka)*(va-Va) / (1-exp(-(va-Va)/Ka)) /(2*Taum_max) : Hz
        betam_axon = (1/Ka)*(-va+Va) / (1-exp((va-Va)/Ka)) /(2*Taum_max) : Hz
        alphah_axon = -(1/Kh)*(va-Vh) / (1-exp((va-Vh)/Kh)) /(2*Tauh_max) : Hz
        betah_axon = (1/Kh)*(va-Vh) / (1-exp(-(va-Vh)/Kh)) /(2*Tauh_max) : Hz
        alphan_axon = (1/Kn)*(va-Vn) / (1-exp(-(va-Vn)/Kn)) /(2*Taun_max) : Hz
        betan_axon = -(1/Kn)*(va-Vn) / (1-exp((va-Vn)/Kn)) /(2*Taun_max): Hz

        alpham_soma = (1/Ka_soma)*(vs-Va_soma) / (1-exp(-(vs-Va_soma)/Ka_soma)) /(2*Taum_max_soma) : Hz
        betam_soma = (1/Ka_soma)*(-vs+Va_soma) / (1-exp((vs-Va_soma)/Ka_soma)) /(2*Taum_max_soma) : Hz
        alphah_soma = -(1/Kh_soma)*(vs-Vh_soma) / (1-exp((vs-Vh_soma)/Kh_soma)) /(2*Tauh_max_soma) : Hz
        betah_soma = (1/Kh_soma)*(vs-Vh_soma) / (1-exp(-(vs-Vh_soma)/Kh_soma)) /(2*Tauh_max_soma) : Hz
        alphan_soma = (1/Kn)*(vs-Vn) / (1-exp(-(vs-Vn)/Kn)) /(2*Taun_max) : Hz
        betan_soma = -(1/Kn)*(vs-Vn) / (1-exp((vs-Vn)/Kn)) /(2*Taun_max): Hz
        '''

        BrianExperiment.__init__(self, eqs, namespace=dict(Cs=Cs,Ca=Ca,Ra=Ra,gL=gL,EL=EL,ENa=ENa,EK=EK,
                                                Ka=Ka,Va=Va,Taum_max=Taum_max,
                                                Kh=Kh,Vh=Vh,Tauh_max=Tauh_max,
                                                Kn=Kn,Vn=Vn,Taun_max=Taun_max,
                                                Ka_soma=Ka_soma, Va_soma=Va_soma, Taum_max_soma=Taum_max_soma,
                                                Kh_soma=Kh_soma, Vh_soma=Vh_soma, Tauh_max_soma=Tauh_max_soma,
                                                gNa_soma=gNa_soma, gNa_axon=gNa_axon,
                                                gK_soma=gK_soma, gK_axon=gK_axon),
                                                gclamp=gclamp, dt=dt)

        self.neuron.vs = EL
        self.neuron.va = EL
        self.neuron.h_soma = 1
        self.neuron.h_axon = 1

# *** The next two ones are probably wrong, because I see no call to BrianExperiment.__init__() ***

class SpatialBrianExperiment(BrianExperiment):
    '''
    A spatially extended neuron model that can be recorded in current-clamp or voltage-clamp.
    '''
    def __init__(self, morphology=None, eqs=None, namespace= None, Cm=None, Ri=None, gclamp = 10*usiemens, dt = 0.1*ms):
        '''
        Parameters
        ----------
        morphology : neuron morphology
        eqs : equations of the model
        namespace : namespace
        Cm : specific membrane capacitance
        Ri : intracellular resistivity
        gclamp : gain of the voltage-clamp
        dt : sampling step (not the same as the simulation time step)
        '''
        eqs += '''
        V = v : volt
        I = CC_switch*Icommand(t-t_start) + Iclamp : amp (point current)
        Iclamp = gclamp*(Vcommand(t-t_start)-V) : amp
        CC_switch : 1
        gclamp : siemens
        t_start : second
        '''
        Board.__init__(self)

        self.dt = dt
        self.gclamp = gclamp

        self.eqs = Equations(eqs)
        neuron = SpatialNeuron(morphology=morphology, model=eqs, Cm=Cm, Ri=Ri,
                               method="exponential_euler",
                               namespace = namespace)
        neuron.CC_switch[0] = 1
        self.neuron = neuron
        self.network = Network(self.neuron)

        self.configure_board()
        self.is_voltage_clamp = False # Initially in current clamp


class AxonalInitiationModel(SpatialBrianExperiment):
    '''
    A spatially extended model with a dendrite and axon, including an initial segment.
    '''
    def __init__(self, gclamp = 1*usiemens, dt = 0.1*ms):
        ### Passive parameters
        EL = -75. * mV
        Cm = 0.9 * uF / cm ** 2
        gL = 1. * (siemens / meter ** 2)
        Ri = 100. * ohm * cm

        ### Morphology: soma at 0, dendrite from 1 to 501, axon from 501 to 1101
        dend_diam = 6 * um
        dend_length = 1500. * um
        axon_diam = 1 * um
        axon_length = 300. * um
        soma_diameter = 30 * um
        morpho = Soma(diameter=soma_diameter)
        dendrite = Cylinder(diameter=dend_diam, length=dend_length, n=500)
        axon = Cylinder(diameter=axon_diam, length=axon_length, n=600)
        morpho.dendrite = dendrite
        morpho.axon = axon

        ### Na channels distribution
        AIS_length = 30. * um
        Na_start = 5. * um
        Na_end = Na_start + AIS_length
        Na_start_idx = morpho.n + dendrite.n + int((Na_start * 2) / um)
        Na_end_idx = Na_start_idx + int(AIS_length / um * 2)

        ### AIS

        # Na channels parameters
        ENa = 70. * mV
        gna = 3500. * (siemens / meter ** 2)

        # K channels parameters
        EK = -90. * mV
        gk = 1500. * (siemens / meter ** 2)

        ## Correction for temperature
        T = 33.
        factor = (1 / 2.8) ** ((T - 23.) / 10.)

        ## Channels kinetics
        # Na+:
        Va = -35. * mV  # Schmidt-Heiber 2010, ~23°C
        Ka = 6. * mV  # Schmidt-Heiber 2010, ~23°C
        Taum_max = factor * 0.15 * ms  # Schmidt-Heiber 2010, ~23°C
        Vh = -67. * mV  # Schmidt-Heiber 2010, ~23°C
        Kh = 6. * mV  # Schmidt-Heiber 2010, ~23°C
        Tauh_max = factor * 5. * ms  # Schmidt-Heiber 2010, ~23°C

        # K+:
        Vn = -73. * mV  # n8 fit from Hallerman 2012
        Kn = 18. * mV  # n8 fit from Hallerman 2012
        Taun_max = 1.4 * ms  # n8 fit from Hallerman 2012

        ### Soma

        # Na channels parameters
        gna_soma = 350. * (siemens / meter ** 2)

        # K channels parameters
        gk_soma = gna_soma

        ## Channels kinetics
        # Na+:
        Va_soma = -29 * mV  # Schmidt-Heiber 2010, ~23°C
        Ka_soma = 7. * mV  # Schmidt-Heiber 2010, ~23°C
        Taum_max_soma = factor * 0.2 * ms  # Schmidt-Heiber 2010, ~23°C
        Vh_soma = -59 * mV  # Schmidt-Heiber 2010, ~23°C
        Kh_soma = 11. * mV  # Schmidt-Heiber 2010, ~23°C
        Tauh_max_soma = factor * 11. * ms  # Schmidt-Heiber 2010, ~23°C

        # Equations
        eqs = '''
        Im = (gL*(EL-v) + gNa*m*h*(ENa-v) + gK*n**8*(EK-v) + gNa_soma*m_soma*h_soma*(ENa-v)) : amp/meter**2
        INa = gNa*m*h*(ENa-v) : amp/meter**2
        IK = gK*n**8*(EK-v) : amp/meter**2

        dm/dt = alpham*(1-m) - betam*m : 1
        dh/dt = alphah*(1-h) - betah*h : 1
        dn/dt = alphan*(1-n) - betan*n : 1

        alpham = (1/Ka)*(v-Va) / (1-exp(-(v-Va)/Ka)) /(2*Taum_max) : Hz
        betam = (1/Ka)*(-v+Va) / (1-exp((v-Va)/Ka)) /(2*Taum_max) : Hz

        alphah = -(1/Kh)*(v-Vh) / (1-exp((v-Vh)/Kh)) /(2*Tauh_max) : Hz
        betah = (1/Kh)*(v-Vh) / (1-exp(-(v-Vh)/Kh)) /(2*Tauh_max) : Hz

        alphan = (1/Kn)*(v-Vn) / (1-exp(-(v-Vn)/Kn)) /(2*Taun_max) : Hz
        betan = -(1/Kn)*(v-Vn) / (1-exp((v-Vn)/Kn)) /(2*Taun_max): Hz

        gNa : siemens/meter**2
        gK : siemens/meter**2

        INa_soma = gNa_soma*m_soma*h_soma*(ENa-v) : amp/meter**2

        dm_soma/dt = alpham_soma*(1-m_soma) - betam_soma*m_soma : 1
        dh_soma/dt = alphah_soma*(1-h_soma) - betah_soma*h_soma : 1

        alpham_soma = (1/Ka_soma)*(v-Va_soma) / (1-exp(-(v-Va_soma)/Ka_soma)) /(2*Taum_max_soma) : Hz
        betam_soma = (1/Ka_soma)*(-v+Va_soma) / (1-exp((v-Va_soma)/Ka_soma)) /(2*Taum_max_soma) : Hz

        alphah_soma = -(1/Kh_soma)*(v-Vh_soma) / (1-exp((v-Vh_soma)/Kh_soma)) /(2*Tauh_max_soma) : Hz
        betah_soma = (1/Kh_soma)*(v-Vh_soma) / (1-exp(-(v-Vh_soma)/Kh_soma)) /(2*Tauh_max_soma) : Hz

        gNa_soma : siemens/meter**2
        '''

        SpatialBrianExperiment.__init__(self,morphology=morpho, eqs=eqs, Cm=Cm, Ri=Ri,
                                             namespace = dict(gL=gL,EL=EL,ENa=ENa,EK=EK,
                                                Ka=Ka,Va=Va,Taum_max=Taum_max,
                                                Kh=Kh,Vh=Vh,Tauh_max=Tauh_max,
                                                Kn=Kn,Vn=Vn,Taun_max=Taun_max,
                                                Ka_soma=Ka_soma, Va_soma=Va_soma, Taum_max_soma=Taum_max_soma,
                                                Kh_soma=Kh_soma, Vh_soma=Vh_soma, Tauh_max_soma=Tauh_max_soma))

        # Soma
        self.neuron.gNa_soma[0] = gna_soma
        self.neuron.gK[0] = gk_soma

        # Initial segment
        initial_segment = morpho.axon[int((Na_start * 2) / um):int((Na_end * 2) / um)]
        self.neuron.gNa[initial_segment] = gna
        self.neuron.gK[initial_segment] = gk

        # Initialisation
        self.neuron.v = EL
        self.neuron.h = 1


if __name__ == '__main__':
    from pylab import plot, show

    #prefs.codegen.target = 'numpy'

    defaultclock.dt = 0.05 * ms
    dt = 0.1 * ms
    amplifier = TwoCompartmentModel2(dt=dt)
    #amplifier = AxonalInitiationModel(dt=dt)

    if True:  # current-clamp
        ntrials = 5
        V = []
        Ic = zeros(int(200 * ms / dt)) * amp
        for ampli in 0.5 * linspace(-1, 1, ntrials) * nA:
            print (ampli)
            Ic[int(10 * ms / dt):int(50 * ms / dt)] = ampli
            V.append(amplifier.acquire('V', I=Ic))

        t = dt * arange(len(Ic))

        # savetxt('data.txt',array(V)/mV)

        for Vi in V:
            plot(t / ms, array(Vi) / mV)

    else:  # voltage-clamp
        ntrials = 10
        I = []
        Vc = ones(int(200 * ms / dt)) * (-75 * mV)
        for ampli in linspace(-75, -55, ntrials) * mV:
            print (ampli)
            Vc[int(10 * ms / dt):int(100 * ms / dt)] = ampli
            I.append(amplifier.acquire('I', V=Vc))

        t = dt * arange(len(Vc))

        for Ii in I:
            plot(t / ms, array(Ii) / nA)

    show()
