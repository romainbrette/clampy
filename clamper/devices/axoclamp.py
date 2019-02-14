# -*- coding: utf-8 -*-
import ctypes
import functools
import os
import logging
import time

__all__ = ['AxoClampChannel', 'AxoClamp']

NO_ERROR = 0

MODE_IZERO = 0
MODE_ICLAMP = 1
MODE_DCC = 2
MODE_HVIC = 3
MODE_DSEVC = 4
MODE_TEVC = 5

FIRST_CHANNEL = 0
SECOND_CHANNEL = 1
BOTH_CHANNELS = 2

AMPLIFIER_MODE = 2

primary_signal_index = {'I': 3,
                        'V': 2}

secondary_signal_index = {'I': 9,
                          'V': 8}


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

    def configure_board(self, theboard, primary=None, secondary=None, command=None):
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

    def acquire(self, *inputs, **outputs):
        pass


class AxoClampChannel(object):
    dll_path = r'C:\Program Files (x86)\Molecular Devices\AxoClamp 900A Commander 1.2'
    all_devices = None
    selected_device = None

    def __init__(self, **kwds):
        self.dll = ctypes.WinDLL(os.path.join(AxoClampChannel.dll_path, 'AxoclampDriver.dll'))
        self.last_error = ctypes.c_uint(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.is_open = ctypes.c_bool(False)
        self.is_connected = ctypes.c_bool(False)
        self.current_channel = ctypes.c_uint(3)
        self.current_mode = ctypes.c_uint(6)     # No Mode
        self.headstage_type = ctypes.c_uint(20)  # No headstage connected
        self.check_error(fail=True)
        self.identification = kwds
        self.select_amplifier()
        volt = 1.
        mV = 1e-3
        nA = 1e-9

        # Temporary values for testing
        self.gain = {'V': 10 * mV / mV,
                     'I': 0.5 * volt / nA,
                     'ICLAMP': 2.5 * volt / nA,
                     'DCC': 2.5 * volt / nA,
                     'HVIC': 2.5 * volt / nA,
                     'DSEVC': 50 * mV / mV,
                     'TEVC': 50 * mV / mV}

    def configure_board(self, theboard, primary=None, secondary=None, command=None):
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

    def acquire(self, *inputs, **outputs):
        if len(inputs) > 2:
            raise IndexError("Not more than two signals can be measured.")
        if len(outputs) != 1:
            raise IndexError('Only one command signal can be passed.')

        outputname = outputs.keys()[0]

        if outputname == 'ICLAMP':
            self.current_clamp()
        elif outputname == 'DCC':
            self.discontinuous_current_clamp()
        elif outputname == 'DSEVC':
            self.discontinuous_single_electrode_voltage_clamp()
        elif outputname == 'HVIC':
            self.high_voltage_current_clamp()
        elif outputname == 'TEVC':
            self.two_electrode_voltage_clamp()
        else:
            raise IndexError("Undefined Mode")

        if self.current_channel == FIRST_CHANNEL:
            self.set_primary_signal(primary_signal_index[inputs[0]], self.current_mode)
            self.board.gain[self.primary] = self.gain[inputs[0]]
            self.set_secondary_signal(secondary_signal_index[inputs[1]], MODE_IZERO)
            self.board.gain[self.secondary] = self.gain[inputs[1]]
        elif self.current_channel == SECOND_CHANNEL:
            self.set_primary_signal(primary_signal_index[inputs[0]], MODE_IZERO)
            self.board.gain[self.primary] = self.gain[inputs[0]]
            self.set_secondary_signal(secondary_signal_index[inputs[1]], self.current_mode)
            self.board.gain[self.secondary] = self.gain[inputs[1]]

        if outputname == 'ICLAMP':
            self.board.gain[self.command] = self.gain['ICLAMP']
        elif outputname == 'DCC':
            self.board.gain[self.command] = self.gain['DCC']
        elif outputname == 'DSEVC':
            self.board.gain[self.command] = self.gain['DSEVC']
        elif outputname == 'HVIC':
            self.board.gain[self.command] = self.gain['HVIC']
        elif outputname == 'TEVC':
            self.board.gain[self.command] = self.gain['TEVC']

        board_inputs = ['primary', 'secondary'][:len(inputs)]  # could be just secondary too
        return self.board.acquire(*board_inputs, command=outputs[outputname])


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

    def select_amplifier(self):
        self.msg_handler = self.dll.AXC_CreateHandle(ctypes.c_bool(False),
                                                     ctypes.byref(self.last_error))
        serial = ctypes.create_string_buffer(16)
        self.dll.AXC_FindFirstDevice(self.msg_handler,
                                     serial,
                                     ctypes.c_uint(16),  # buffer size SN: 16
                                     ctypes.byref(self.last_error))
        self.dll.AXC_DestroyHandle(self.msg_handler)
        self.msg_handler = self.dll.AXC_CreateHandle(ctypes.c_bool(False),
                                                     ctypes.byref(self.last_error))
        if not self.dll.AXC_IsDeviceOpen(self.msg_handler,
                                         ctypes.byref(self.is_open),
                                         ctypes.byref(self.last_error)):
            self.check_error()
        if not self.is_open:
            if not self.dll.AXC_OpenDevice(self.msg_handler,
                                           serial,
                                           ctypes.c_bool(True),
                                           ctypes.byref(self.last_error)):
                self.check_error(True)

        if not self.dll.AXC_Reset(self.msg_handler,
                                  ctypes.byref(self.last_error)):
            self.check_error()
        #time.sleep(1.5)
        # auxiliary = False
        # if not self.dll.AXC_IsHeadstagePresent(self.msg_handler,
        #                                        ctypes.byref(self.is_connected),
        #                                        ctypes.c_int(SECOND_CHANNEL),
        #                                        ctypes.c_bool(auxiliary),
        #                                        ctypes.byref(self.last_error)):
        #     self.check_error()
        # if self.is_connected:
        #     if not self.dll.AXC_GetHeadstageType(self.msg_handler,
        #                                          ctypes.byref(self.headstage_type),
        #                                          ctypes.c_int(SECOND_CHANNEL),
        #                                          ctypes.c_bool(auxiliary),
        #                                          ctypes.byref(self.last_error)):
        #         self.check_error(True)
        #
        # print("Testing type: ", self.headstage_type)
        #####Both channels are type3-headstage: "HS-9A x0.1"

        if not self.dll.AXC_SetSyncOutput(self.msg_handler,
                                          ctypes.c_int(AMPLIFIER_MODE),
                                          ctypes.byref(self.last_error)):
            self.check_error()

    def start_patch(self, pulse_amplitude=1e-2, pulse_frequency=1e-2):  # Not clear what the units are for frequency
        '''
        Initialize the patch clamp procedure (in bath)
        '''
        # Set in voltage clamp
        self.discontinuous_single_electrode_voltage_clamp()

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

    def set_primary_signal(self, signal, mode):
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(FIRST_CHANNEL),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_secondary_signal(self, signal, mode):
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(SECOND_CHANNEL),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_scaled_output_signal_gain(self, gain, channel, mode):
        if not self.dll.AXC_SetScaledOutputGain(self.msg_handler,
                                                ctypes.c_double(gain),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    def current_clamp(self):
        self.current_mode = MODE_ICLAMP
        self.current_channel = FIRST_CHANNEL
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def discontinuous_current_clamp(self):
        self.current_mode = MODE_DCC
        self.current_channel = FIRST_CHANNEL
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def discontinuous_single_electrode_voltage_clamp(self):
        self.current_mode = MODE_DSEVC
        self.current_channel = FIRST_CHANNEL
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def high_voltage_current_clamp(self):
        self.current_mode = MODE_HVIC
        self.current_channel = SECOND_CHANNEL
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def two_electrode_voltage_clamp(self):
        self.current_mode = MODE_TEVC
        self.current_channel = SECOND_CHANNEL
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def null_current(self):
        self.current_mode = MODE_IZERO
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(FIRST_CHANNEL),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(SECOND_CHANNEL),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def switch_holding(self, enable):
        if not self.dll.AXC_SetHoldingEnable(self.msg_handler,
                                             ctypes.c_bool(enable),
                                             ctypes.c_uint(self.current_channel),
                                             ctypes.c_uint(self.current_mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def set_holding(self, value):
        if not self.dll.AXC_SetHoldingLevel(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(self.current_channel),
                                            ctypes.c_uint(self.current_mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def auto_pipette_offset(self):  # Set for all modes
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(MODE_ICLAMP),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_AutoPipetteOffset(self.msg_handler,
                                              ctypes.c_uint(self.current_channel),
                                              ctypes.c_uint(MODE_ICLAMP),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(self.current_channel),
                                    ctypes.c_uint(self.current_mode),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def set_bridge_balance(self, state):
        if not self.dll.AXC_SetBridgeEnable(self.msg_handler,
                                            ctypes.c_bool(state),
                                            ctypes.c_uint(self.current_channel),
                                            ctypes.c_uint(self.current_mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_SetCapNeutEnable(self.msg_handler,
                                            ctypes.c_bool(state),
                                            ctypes.c_uint(self.current_channel),
                                            ctypes.c_uint(self.current_mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_bridge_resistance(self):
        resistance = ctypes.c_double(0.)
        if not self.dll.AXC_GetBridgeLevel(self.msg_handler,
                                           ctypes.byref(resistance),
                                           ctypes.c_uint(self.current_channel),
                                           ctypes.c_uint(self.current_mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()
        return resistance.value

    def auto_bridge_balance(self):
        if not self.dll.AXC_AutoBridge(self.msg_handler,
                                       ctypes.c_uint(self.current_channel),
                                       ctypes.c_uint(self.current_mode),
                                       ctypes.byref(self.last_error)):
            self.check_error()
        return self.get_bridge_resistance()

    def zap(self): #No built-in zap function
        zap_amplitude = 1.
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(zap_amplitude),
                                              ctypes.c_uint(self.current_channel),
                                              ctypes.c_uint(self.current_mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_Pulse(self.msg_handler,
                                  ctypes.c_uint(self.current_channel),
                                  ctypes.c_uint(self.current_mode),
                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_zap_duration(self, duration):
        if not self.dll.AXC_SetPulseDuration(self.msg_handler,
                                             ctypes.c_double(duration),
                                             ctypes.c_uint(self.current_channel),
                                             ctypes.c_uint(self.current_mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulse Duration")

    def get_meter_value(self):
        value = ctypes.c_double(0.)
        auxiliary = False
        if not self.dll.AXC_GetRf(self.msg_handler,
                                  ctypes.byref(value),
                                  ctypes.c_uint(self.current_channel),
                                  ctypes.c_bool(auxiliary),
                                  ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def switch_resistance_meter(self, enable):
        custom_set_Rf = 1.0e+8
        custom_set_Ci = 10.0e-12
        if not self.dll.AXC_SetCustomHeadstageValues(self.msg_handler,
                                                     ctypes.c_double(custom_set_Rf),
                                                     ctypes.c_double(custom_set_Ci),
                                                     ctypes.c_bool(enable),
                                                     ctypes.c_uint(self.current_channel),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    def switch_pulses(self, enable):
        if not self.dll.AXC_SetTestSignalEnable(self.msg_handler,
                                                ctypes.c_bool(enable),
                                                ctypes.c_uint(self.current_channel),
                                                ctypes.c_uint(self.current_mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    def set_pulses_amplitude(self, amplitude):
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(amplitude),
                                              ctypes.c_uint(self.current_channel),
                                              ctypes.c_uint(self.current_mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    def set_pulses_frequency(self, frequency):
        if not self.dll.AXC_SetTestSignalFrequency(self.msg_handler,
                                                   ctypes.c_double(frequency),
                                                   ctypes.c_uint(self.current_channel),
                                                   ctypes.c_uint(self.current_mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    def close(self):
        self.dll.AXC_CloseDevice(self.msg_handler,
                                 ctypes.byref(self.last_error))
        self.dll.AXC_DestroyHandle(self.msg_handler)
        self.msg_handler = None
        self.msg_handler = None


if __name__ == '__main__':
    from ni import *
    from pylab import *

    ms = 0.001
    pA = 1e-12
    mV = 0.001
    volt = 1
    nA = 1e-9
    dt = 0.1 * ms

    board = NI()
    board.sampling_rate = float(10000.)
    board.set_analog_input('primary', channel=0)
    board.set_analog_input('secondary', channel=1)
    board.set_analog_output('command', channel=0)

    amp = AxoClampChannel()
    amp.configure_board(board, primary='primary', secondary='secondary', command='command')

    Ic = zeros(int(1000 * ms / dt))
    Ic[int(130 * ms / dt):int(330 * ms / dt)] += 500 * pA
    Vc = zeros(int(1000 * ms / dt))
    Vc[int(130 * ms / dt):int(330 * ms / dt)] = 20 * mV
    amp.set_bridge_balance(True)
    Rs = amp.auto_bridge_balance()
    print (Rs / 1e6)
    Vm, Im = amp.acquire('V', 'I', ICLAMP=Ic)
    # Im, Vm = amp.acquire('I', 'V', I = Ic)
    # Vm, Im = amp.acquire('V', 'I', V=Vc)

    R = (Vm[len(Vm) / 4] - Vm[0]) / Im[len(Im) / 4]
    print(R / 1e6)

    subplot(211)
    plot(array(Vm) / (mV))
    subplot(212)
    plot(Im / pA)
    show()