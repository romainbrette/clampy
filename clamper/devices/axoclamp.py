# -*- coding: utf-8 -*-
import ctypes
import functools
import os
import logging
import time

__all__ = ['AxoClampChannel', 'AxoClamp']

NO_ERROR = 0

primary_signal_ICLAMP_index = {'V' : 2,
                           'I' : 3}

primary_signal_dSEVC_index = {'V' : 2,
                           'I' : 3}

primary_signal_index = {'I' : primary_signal_ICLAMP_index,
                        'V' : primary_signal_dSEVC_index}

secondary_signal_ICLAMP_index = {'V' : 8,
                             'I' : 9}

secondary_signal_TEVC_index = {'V' : 8,
                             'I' : 9}

secondary_signal_index = {'I' : secondary_signal_ICLAMP_index,
                          'V' : secondary_signal_TEVC_index}

def _identify_amplifier(model, serial):
    if model.value == 0:  # 900A
        logging.info(('Found a AxoClamp 900A (Serial: {}').format(serial.value))
        return {'model': '900A', 'serial': serial.value}
    else:
        raise AssertionError('Unknown model')

class AxoClamp(object):
    def __init__(self, *channels):
        self.channel = channels
        if len(channels) == 0:  # assumes a 2-channel axoclamp
            for i in range(2):
                self.channel.append(AxoClampChannel(channel=i + 1))

    def configure_board(self, theboard, primary = None, secondary = None, command = None):
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

    def acquire(self, *inputs, **outputs):
        pass

class AxoClampChannel(object):
    #Add environment path for other dll in Settings
    dll_path = r'C:\Program Files (x86)\Molecular Devices\AxoClamp 900A Commander 1.2'
    all_devices = None
    selected_device = None

    def __init__(self, **kwds):
        self.dll = ctypes.WinDLL(os.path.join(AxoClampChannel.dll_path,'AxoclampDriver.dll'))
        self.last_error = ctypes.c_int(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.device_state = ctypes.c_bool(False)
        self.msg_handler = self.dll.AXC_CreateHandle(ctypes.c_bool(True),
                                                     ctypes.byref(self.last_error))  # Demo Mode: False
        self.check_error(fail=True)
        if AxoClampChannel.all_devices is None:
            AxoClampChannel.all_devices = self.find_amplifiers()
        self.identification = kwds
        self.select_amplifier()

        volt = 1.
        mV = 1e-3
        nA = 1e-9
        self.gain = {'V': 10 * mV / mV,
                     'I': 0.5 * volt / nA,
                     'Ic': 2.5 * volt / nA,  # command current
                     'Ve': 1 * mV / mV,
                     'Vext': 50 * mV / mV,
                     '100V': 500 * mV / mV,
                     'Iext': 2.5 * volt / nA,
                     'Aux1': None,
                     'Aux2': None}

    def configure_board(self, theboard, primary = None, secondary = None, command = None):
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

    def acquire(self, *inputs, **outputs):
        if len(inputs)>2:
            raise IndexError("Not more than two signals can be measured.")
        if len(outputs)!=1:
            raise IndexError('Only one command signal can be passed.')

        outputname = outputs.keys()[0]
        if outputname == 'I':
            self.current_clamp()
            set_mode1 = 1
            set_mode2 = 1
        elif outputname == 'V':
            self.voltage_clamp() # 1 electrode VC
            set_mode1 = 4
        elif outputname == 'V2':
            self.two_electrode_voltage_clamp() # 2 electrode VC
            set_mode2 = 5
        else:
            raise IndexError("Output command must be I or V or V2.")

        self.set_primary_signal_gain(1., set_mode1)
        self.set_secondary_signal_gain(1., set_mode2)

        # TODO: possibly switch primary and secondary depending on the signal name
        self.set_primary_signal(primary_signal_index[outputname][inputs[0]], set_mode1)
        self.board.gain[self.primary] = self.gain[inputs[0]]
        if len(inputs) == 2:
            self.set_secondary_signal(secondary_signal_index[outputname][inputs[1]], set_mode2)
            self.board.gain[self.secondary] = self.gain[inputs[1]]

        if outputname == 'I':
            self.board.gain[self.command] = self.gain['Ic']
        elif outputname == 'V':
            self.board.gain[self.command] = self.gain['Vext']

        board_inputs = ['primary', 'secondary'][:len(inputs)] # could be just secondary too
        return self.board.acquire(*board_inputs, command = outputs[outputname])

    def check_error(self, fail=False):
        if self.last_error.value != NO_ERROR:
            self.dll.AXC_BuildErrorText(self.msg_handler,
                                        self.last_error,
                                        self.error_msg,
                                        ctypes.c_uint(256))
            full_error = ('An error occurred while communicating with the '
                          'AxoClamp amplifier: {}'.format(self.error_msg.value))
            if fail:
                raise IOError(full_error)
            else:
                logging.warn(full_error)
            self.last_error.value = NO_ERROR

    def find_amplifiers(self):
        model = ctypes.c_uint(0) #Axoclamp 900A (Currently no other model)
        serial = ctypes.create_string_buffer(16)
        devices = []

        if self.dll.AXC_FindFirstDevice(self.msg_handler,
                                        serial,
                                        ctypes.c_uint(16),  # buffer size SN: 16
                                        ctypes.byref(self.last_error)):
            devices.append(_identify_amplifier(model, serial))
            print("Find Amplifiers")

        else:
            self.check_error()


        while self.dll.AXC_FindNextDevice(self.msg_handler,
                                          serial,
                                          ctypes.c_uint(16),  # buffer size
                                          ctypes.byref(self.last_error)):
            devices.append(_identify_amplifier(model, serial))

        return devices

    def select_amplifier(self):
        """""
        axoclamps = []
        for axoclamp in AxoClampChannel.all_devices:
            if all(axoclamp.get(key, None) == value
                   for key, value in self.identification.iteritems()):
                axoclamps.append(axoclamp)
        if len(axoclamps) == 0:
            raise RuntimeError('No device identified via {} found'.format(self.identification))
        elif len(axoclamps) > 1:
            raise RuntimeError('{} devices identified via {} found'.format(len(axoclamps),
                                                                           self.identification))
        axoclamp = axoclamps[0]
        if axoclamp['model'] == '900A':
            serial = axoclamp['serial']
        """


        serial = ctypes.create_string_buffer(16)

        self.dll.AXC_FindFirstDevice(self.msg_handler,
                                     serial,
                                     ctypes.c_uint(16),  # buffer size SN: 16
                                     ctypes.byref(self.last_error))

        print("Serial Number: ", serial.value)

        #####HID device not found##### Not sure why?
        #self.dll.AXC_DestroyHandle(self.msg_handler)
        #self.msg_handler = self.dll.AXC_CreateHandle(ctypes.c_bool(False),
        #                                             ctypes.byref(self.last_error))

        #if not self.dll.AXC_IsDeviceOpen(self.msg_handler,
        #                                 ctypes.byref(self.device_state),
        #                                 ctypes.byref(self.last_error)):
        #
        #    self.check_error()

        #if not self.device_state:

        if not self.dll.AXC_OpenDevice(self.msg_handler,
                                       serial,
                                       ctypes.c_bool(True),
                                       ctypes.byref(self.last_error)):
            print("Open Device: ", self.last_error)
            self.check_error()
        #AxoClampChannel.selected_device = self

    def start_patch(self, pulse_amplitude=1e-2, pulse_frequency=1e-2): # Not clear what the units are for frequency
        '''
        Initialize the patch clamp procedure (in bath)
        '''
        # Set in voltage clamp
        self.voltage_clamp()

        # Disable resistance metering (because of pulses)
        self.switch_resistance_meter(False)

        # Disable pulses
        self.switch_pulses(False)

        # Set pulse frequency and amplitude
        self.set_pulses_amplitude(pulse_amplitude)
        self.set_pulses_frequency(pulse_frequency)

        # Set zap duration
        self.set_zap_duration(1)  # ms

        # Automatic offset
        self.auto_pipette_offset()

        # Set holding potential
        self.switch_holding(True)
        self.set_holding(0.)

        # Enable resistance metering
        self.switch_resistance_meter(True)

    def resistance(self):
        '''
        Returns resistance
        '''
        # Get resistance (assuming resistance metering is on)
        return self.get_meter_value()

    def stop_patch(self):
        '''
        Stops patch clamp procedure
        '''
        # Disable resistance metering
        self.switch_resistance_meter(False)
        # Disable holding
        self.switch_holding(False)
        # Disable pulses
        self.switch_pulses(False)
        # Mode I=0
        self.null_current()

    # **** Signal settings ****

    
    def set_primary_signal(self, signal, mode):
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(0),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Primary Signal")

    
    def set_primary_signal_gain(self, gain, mode):
        if not self.dll.AXC_SetScaledOutputGain(self.msg_handler,
                                                ctypes.c_double(gain),
                                                ctypes.c_uint(0),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Primary Signal Gain")

    
    def set_secondary_signal(self, signal, mode):
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(1),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Secondary Signal")

    
    def set_secondary_signal_gain(self, gain, mode):
        if not self.dll.AXC_SetScaledOutputGain(self.msg_handler,
                                                ctypes.c_double(gain),
                                                ctypes.c_uint(1),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Secondary Signal Gain")

    # **** Recording modes ****

    
    # Discontinuous single‐electrode voltage clamp mode
    def voltage_clamp(self):
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(0),
                                    ctypes.c_uint(4),
                                    ctypes.byref(self.last_error)):
            self.check_error()
            print("Voltage Clamp")

    
    # Two‐electrode voltage clamp mode
    def two_electrode_voltage_clamp(self):
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(1),
                                    ctypes.c_uint(5),
                                    ctypes.byref(self.last_error)):
            self.check_error()
            print("Two Electrode Voltage Clamp")

    
    def current_clamp(self):
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(2),
                                    ctypes.c_uint(1),
                                    ctypes.byref(self.last_error)):
            self.check_error()
            print("Current Clamp")

     # I=0
    def null_current(self):
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(2),
                                    ctypes.c_uint(0),
                                    ctypes.byref(self.last_error)):
            self.check_error()
            print("Null Current")

    # **** Voltage clamp ****
    
    def switch_holding(self, enable): # True if voltage is clamped. Channel 0, mode 4 (1 electrode)
        if not self.dll.AXC_SetHoldingEnable(self.msg_handler,
                                             ctypes.c_bool(enable),
                                             ctypes.c_uint(0),
                                             ctypes.c_uint(4),
                                             ctypes.byref(self.last_error)):
            self.check_error()
            print("Switch Holding")

    
    def set_holding(self, value): # Voltage-clamp value. Channel 0, mode 4 (1 electrode)
        if not self.dll.AXC_SetHoldingLevel(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(0),
                                            ctypes.c_uint(4),
                                            ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Holding")

    # **** Compensation ****

    
    def auto_pipette_offset(self):  # Set for all modes
        if not self.dll.AXC_AutoPipetteOffset(self.msg_handler,
                                              ctypes.c_uint(2),
                                              ctypes.c_uint(7),
                                              ctypes.byref(self.last_error)):
            self.check_error()
            print("Auto Pipette Offset")

    
    def set_bridge_balance(self, state):
        if not self.dll.AXC_SetBridgeEnable(self.msg_handler,
                                            ctypes.c_bool(state),
                                            ctypes.c_uint(0),
                                            ctypes.c_uint(1),
                                            ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Bridge Balance")

    
    def get_bridge_resistance(self):
        resistance = ctypes.c_double(0.)
        if not self.dll.AXC_GetBridgeLevel(self.msg_handler,
                                                  ctypes.byref(resistance),
                                                  ctypes.c_uint(0),
                                                  ctypes.c_uint(1),
                                                  ctypes.byref(self.last_error)):
            print("Testing: ", self.last_error)
            self.check_error()
            print("Get Bridge Resistance")
        return resistance.value

    
    def auto_bridge_balance(self):
        if not self.dll.AXC_AutoBridge(self.msg_handler,
                                       ctypes.c_uint(0),
                                       ctypes.c_uint(1),
                                       ctypes.byref(self.last_error)):
            print("Testing: ", self.last_error)
            self.check_error()
            print("Auto Bridge Balance")
        return 0
        #self.get_bridge_resistance()

    # **** Zap ****
    
    def zap(self): #No built-in zap function
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(1.),
                                              ctypes.c_uint(0),
                                              ctypes.c_uint(4),
                                              ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulse Amplitude")
        if not self.dll.AXC_Pulse(self.msg_handler,
                                  ctypes.c_uint(0),
                                  ctypes.c_uint(4),
                                  ctypes.byref(self.last_error)):
            self.check_error()
            print("Pulse")

    
    def set_zap_duration(self, duration):
        if not self.dll.AXC_SetPulseDuration(self.msg_handler,
                                             ctypes.c_double(duration),
                                             ctypes.c_uint(0),
                                             ctypes.c_uint(4),
                                             ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulse Duration")

    # **** Measuring V and R ****
    
    def get_meter_value(self):
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetRf(self.msg_handler,
                                  ctypes.byref(value),
                                  ctypes.c_uint(0),
                                  ctypes.c_bool(True),
                                  ctypes.byref(self.last_error)):
            self.check_error()
            print("Get Rf")
        return value.value

    
    def switch_resistance_meter(self, enable):
        if not self.dll.AXC_SetCustomHeadstageValues(self.msg_handler,
                                                     ctypes.c_bool(enable),
                                                     ctypes.c_double(0.),
                                                     ctypes.c_double(0.),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Custom Headstage Values")

    # **** Repeated pulses ****
    
    def switch_pulses(self, enable):
        if not self.dll.AXC_SetTestSignalEnable(self.msg_handler,
                                                ctypes.c_bool(enable),
                                                ctypes.c_uint(0),
                                                ctypes.c_uint(4),
                                                ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Test Signal Enable")

    
    def set_pulses_amplitude(self, amplitude):
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(amplitude),
                                              ctypes.c_uint(0),
                                              ctypes.c_uint(4),
                                              ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulses Amplitude")

    
    def set_pulses_frequency(self, frequency):
        if not self.dll.AXC_SetTestSignalFrequency(self.msg_handler,
                                                   ctypes.c_double(frequency),
                                                   ctypes.c_uint(0),
                                                   ctypes.c_uint(4),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulses Frequency")

    def close(self):
        self.dll.AXC_CloseDevice(self.msg_handler,
                                 ctypes.byref(self.last_error))
        self.dll.AXC_DestroyHandle(self.msg_handler)
        self.msg_handler = None

if __name__ == '__main__':
    from ni import *
    from pylab import *
    ms = 0.001
    pA = 1e-12
    mV = 0.001
    volt = 1
    nA = 1e-9
    dt = 0.1*ms

    board = NI()
    board.sampling_rate = float(10000.)
    board.set_analog_input('primary', channel = 0)
    board.set_analog_input('secondary', channel = 1)
    board.set_analog_output('command', channel = 0)

    amp = AxoClampChannel()
    amp.configure_board(board, primary = 'primary', secondary = 'secondary', command = 'command')

    Ic = zeros(int(1000*ms/dt))
    Ic[int(130*ms/dt):int(330*ms/dt)] += 500*pA
    Vc = zeros(int(1000*ms/dt))
    Vc[int(130 * ms / dt):int(330 * ms / dt)] = 20*mV
    amp.set_bridge_balance(True)
    Rs = amp.auto_bridge_balance()
    print (Rs / 1e6)

    Vm, Im = amp.acquire('V','I', I = Ic)
    #Im, Vm = amp.acquire('I', 'V', I = Ic)
    #Vm, Im = amp.acquire('V', 'I', V=Vc)

    R = (Vm[len(Vm)/4] - Vm[0])/Im[len(Im)/4]
    print( R / 1e6)

    subplot(211)
    plot(array(Vm)/(mV))
    subplot(212)
    plot(Im/pA)
    show()