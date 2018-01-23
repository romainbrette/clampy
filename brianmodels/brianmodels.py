# coding: utf-8
'''
Brian models that can be run as if they were an amplifier
'''

__all__ = ['BrianExperiment', 'TwoCompartmentModel', 'SpatialBrianExperiment', 'AxonalInitiationModel']

from brian2 import *

class BrianExperiment(object):
    '''
    A neuron model that can be recorded in current-clamp or voltage-clamp.

    The equations must include V (membrane potential) and I (injected current).
    '''
    def __init__(self, eqs = None, namespace = None, gclamp = 10*usiemens, dt = 0.1*ms):
        '''
        Parameters
        ----------
        eqs : Brian equations of the model
        namespace : namespace of the model
        gclamp : gain of the voltage-clamp
        dt : sampling step (not the same as the simulation time step)
        '''
        self.eqs = eqs+'''
        I = Icommand(t-t_start) + Iclamp : amp
        Iclamp = gclamp*(Vcommand(t-t_start)-V) : amp
        gclamp : siemens
        t_start : second
        '''
        self.dt = dt
        self.gclamp = gclamp
        self.neuron = NeuronGroup(1, self.eqs, namespace=namespace, method='exponential_euler')
        self.network = Network(self.neuron)

    def acquire(self, *inputs, **outputs):
        '''
        Send commands and acquire signals.

        Parameters
        ----------
        inputs
            A list of input variables to acquire. From: V, I, Ve (electrode potential)
            A maximum of two inputs.
        outputs
            A dictionary of commands. From: V, I.
            Only one command!
        '''
        # A few checks
        if len(inputs)>2:
            raise IndexError("Not more than two signals can be measured.")
        if len(outputs)!=1:
            raise IndexError('Only one command signal can be passed.')

        outputname = outputs.keys()[0]
        results = dict()
        if outputname == 'I': # Current clamp
            self.neuron.t_start = self.network.t
            Icommand = TimedArray(outputs['I'], dt = self.dt)
            Vcommand = TimedArray([0*volt], dt=self.dt)
            self.neuron.gclamp[0] = 0*siemens
            self.monitor = StateMonitor(self.neuron, 'V', record=[0], dt = self.dt)
            self.network.add(self.monitor)
            self.network.run(len(outputs['I'])*self.dt)
            results['V'] = self.monitor.V[0]
            results['I'] = outputs['I']
            self.network.remove(self.monitor)
        elif outputname == 'V': # Voltage clamp
            self.neuron.t_start = self.network.t
            Icommand = TimedArray([0 * amp], dt=self.dt)
            Vcommand = TimedArray(outputs['V'], dt = self.dt)
            self.neuron.gclamp[0] = self.gclamp
            self.monitor = StateMonitor(self.neuron, 'Iclamp', record=[0], dt = self.dt)
            self.network.add(self.monitor)
            self.network.run(len(outputs['V'])*self.dt)
            results['V'] = outputs['V']
            results['I'] = self.monitor.Iclamp[0]
            self.network.remove(self.monitor)
        else:
            raise IndexError("Output command must be I or V.")

        # Fills in other values
        results['Ve'] = results['V']
        results['Vext'] = results['V']
        results['100V'] = results['V']
        results['Ic'] = results['I']
        results['Iext'] = results['I']

        if len(inputs) == 1:
            return results[inputs[0]]
        else:
            return [results[x] for x in inputs]

class TwoCompartmentModel(BrianExperiment):
    '''
    A two compartment model with soma and AIS.
    '''
    def __init__(self, gclamp = 10*usiemens, dt = 0.1*ms):
        eqs = '''
            dvs/dt = (gL*(EL-vs) + INa_soma + IK_soma + Ia + I) /Cs : volt
            V = vs : volt
            dva/dt = (INa_axon + IK_axon - Ia) /Ca : volt
            Ia = (va-vs)/Ra : amp

            INa_axon = gNa_axon*(ENa-va)*m_axon*h_axon : amp
            dm_axon/dt = (1/(1+exp((v12-va)/ka))-m_axon)/taum : 1
            dh_axon/dt = (1/(1+exp((va-v12_inact)/ka))-h_axon)/tauha : 1

            INa_soma = gNa_soma*(ENa-vs)*m_soma*h_soma : amp
            dm_soma/dt = (1/(1+exp((v12-vs)/ka))-m_soma)/taum : 1
            dh_soma/dt = (1/(1+exp((va-v12_inact)/ka))-h_soma)/tauhs : 1

            IK_axon = gK_axon*(EK-va)*n_axon : amp
            dn_axon/dt = (1/(1+exp((v12_K-va)/ka))-n_axon)/tauha : 1

            IK_soma = gK_soma*(EK-vs)*n_soma : amp
            dn_soma/dt = (1/(1+exp((v12_K-vs)/ka))-n_soma)/tauhs : 1

            tauhs = (taumax-taumin)*1/(1+exp((vs - x0)/ c)) + taumin :second
            tauha = (taumax-taumin)*1/(1+exp((va - x0)/ c)) + taumin :second
        '''

        # Na channels
        ENa = 60 * mV
        v12 = -30 * mV
        ka = 6 * mV
        taum = 50 * us
        v12_inact = -40 * mV

        # K channels
        EK = -90 * mV
        v12_K = -20 * mV

        # Somatic compartment
        Cs = 300 * pF  # This is an effective capacitance for layer 5 pyramidal cell (Arsiero et al 2007)
        EL = -70 * mV
        tau = 20 * ms
        gL = Cs / tau
        gNa_soma = 60 * gL
        gK_soma = gNa_soma * 2

        # Axonal compartment
        d = 1 * um
        l = 40 * um
        Ca = (1 * uF / cm ** 2) * pi * d * l * 2
        gNa_axon = 5 * nS / um ** 2 * pi * d * l
        gK_axon = gNa_axon * 3

        # Coupling
        Ri = 150 * ohm * cm
        x = 2 * um  # Start of AIS
        Ra = 4 * Ri / (pi * d ** 2) * x

        c = 10. * mV
        taumin = 1. * ms
        taumax = 3. * ms
        x0 = -30. * mV

        namespace = dict(ENa=ENa, v12=v12,ka=ka,taum=taum,v12_inact=v12_inact,
                         EK=EK,v12_K=v12_K,
                         Cs=Cs,EL=EL,gL=gL,gNa_soma=gNa_soma,gK_soma=gK_soma,
                         Ca=Ca,gNa_axon=gNa_axon,gK_axon=gK_axon,
                         Ri=Ri,Ra=Ra,
                         c=c,taumin=taumin,taumax=taumax,x0=x0)

        BrianExperiment.__init__(self,eqs,namespace,gclamp,dt)

        self.neuron.vs = EL
        self.neuron.va = EL
        self.neuron.h_soma = 1
        self.neuron.h_axon = 1

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
        self.dt = dt
        self.gclamp = gclamp

        neuron = SpatialNeuron(morphology=morphology, model=eqs, Cm=Cm, Ri=Ri,
                               method="exponential_euler",
                               namespace = namespace)
        neuron.CC_switch[0] = 1
        self.neuron = neuron
        self.network = Network(self.neuron)

class AxonalInitiationModel(SpatialBrianExperiment):
    '''
    A spatially extended model with a dendrite and axon, including an initial segment.
    '''
    def __init__(self, gclamp = 1*usiemens, dt = 0.1*ms):
        ### Passive parameters
        EL = -75. * mV
        Cm = 0.9 * uF / cm ** 2
        gL = 1. * (siemens / meter ** 2)
        Ri = 150. * ohm * cm

        ### Morphology: soma at 0, dendrite from 1 to 501, axon from 501 to 1101
        dend_diam = 6 * um
        dend_length = 500. * um
        axon_diam = 1 * um
        axon_length = 300. * um
        soma_diameter = 0.00015 * um
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
        gna = 3000. * (siemens / meter ** 2)

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
        Kh = 9. * mV  # Schmidt-Heiber 2010, ~23°C
        Tauh_max = factor * 10. * ms  # Schmidt-Heiber 2010, ~23°C

        # K+:
        Vn = -73. * mV  # n8 fit from Hallerman 2012
        Kn = 18. * mV  # n8 fit from Hallerman 2012
        Taun_max = 1.4 * ms  # n8 fit from Hallerman 2012

        ### Soma

        # Na channels parameters
        gna_soma = 250000 * 1e-12 * siemens / morpho.area

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

    prefs.codegen.target = 'numpy'

    defaultclock.dt = 0.05 * ms
    dt = 0.1 * ms
    amplifier = AxonalInitiationModel(dt=dt)

    if True:  # current-clamp
        ntrials = 5
        V = []
        Ic = zeros(int(200 * ms / dt)) * amp
        for ampli in 0.3 * linspace(-1, 1, ntrials) * nA:
            print ampli
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
            print ampli
            Vc[int(10 * ms / dt):int(100 * ms / dt)] = ampli
            I.append(amplifier.acquire('I', V=Vc))

        t = dt * arange(len(Vc))

        for Ii in I:
            plot(t / ms, array(Ii) / nA)

    show()