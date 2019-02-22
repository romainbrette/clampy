# -*- coding: utf-8 -*-
"""
Basic Interface to the Axoclamp 900A amplifier.

Note that the AxoClamp Commander should *not* be running in order to use the device.

Gains according to the manual:
I-Clamp, DCC: 1, 10, or 100 nA/V (depends on headstage)
HVIC : 10, 100, or 1000 nA/V (depends on headstage).
dSEVC : 20 mV/V
dSEVC AC voltage‐clamp gain:   0.003–30 nA/mV, 0.03–300 nA/mV, 0.3–3000 nA/mV (depends on headstage).
TEVC : 20 mV/V

In ni.py, I always use volt/measured unit.

TODO:
    We should be able to set all the gains (maybe with the table directly)

    Use this to get the gain: AXC_GetSignalScaleFactor
"""
import ctypes
import logging
import os

__all__ = ['AxoClamp900A']

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

AMPLIFIER_MODE = 2 # what's this?

# Signals
SIGNAL_ID_XICMD1      = 0
SIGNAL_ID_ICMD1       = 1
SIGNAL_ID_10V1        = 2
SIGNAL_ID_I1          = 3
SIGNAL_ID_MON         = 4
SIGNAL_ID_RMP         = 5
SIGNAL_ID_XICMD2      = 6
SIGNAL_ID_ICMD2       = 7
SIGNAL_ID_10V2        = 8
SIGNAL_ID_I2          = 9
SIGNAL_ID_DIV10V2     = 10
SIGNAL_ID_DIV10I2     = 11
SIGNAL_ID_XVCMD       = 12
SIGNAL_ID_VCMD        = 13
SIGNAL_ID_10AUX1      = 14
SIGNAL_ID_10AUX2      = 15
SIGNAL_ID_10mV        = 16
SIGNAL_ID_GND         = 17


def _identify_amplifier(model, serial):
    if model.value == 0:  # 900A
        logging.info(('Found a AxoClamp 900A (Serial: {}').format(serial.value))
        return {'model': '900A', 'serial': serial.value}
    else:
        raise AssertionError('Unknown model')


class AxoClamp900A(object):
    """
    Device representing an Axoclamp 900A amplifier, which has two channels.
    """
    dll_path = r'C:\Program Files (x86)\Molecular Devices\AxoClamp 900A Commander 1.2' # We need something more robust!

    def __init__(self, **kwds):
        self.dll = ctypes.WinDLL(os.path.join(AxoClamp900A.dll_path, 'AxoclampDriver.dll'))
        self.last_error = ctypes.c_uint(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.is_open = ctypes.c_bool(False)
        self.is_connected = ctypes.c_bool(False)
        self.current_mode = [0,0] #[ctypes.c_uint(6), ctypes.c_uint(6)]
        self.headstage_type = ctypes.c_uint(20)  # No headstage connected
        self.check_error(fail=True)
        self.select_amplifier()

        volt = 1.
        mV = 1e-3
        nA = 1e-9

        self.gain = {'Vc': 1./(20 * mV / volt)}

        # Sets gains according to headstage Rf
        multiplier = self.get_Rf(FIRST_CHANNEL)/1e6
        #print('Rf on first channel: {}'.format(multiplier))
        self.gain['Ic1'] = multiplier * 0.01*volt/nA
        multiplier = self.get_Rf(SECOND_CHANNEL)/1e6
        #print('Rf on second channel: {}'.format(multiplier))
        self.gain['Ic2'] = multiplier * 0.01*volt/nA
        # HVIC gain not set here

        # Output gains
        self.gain['V'] = 10*mV/mV
        self.gain['I'] = 0.1*volt/nA

    def configure_board(self, theboard, I1=None, I2=None, output1=None, output2=None,
                        Ic1=None, Ic2=None, Vc=None):
        '''
        Configures the wiring with the acquisition board, for all analog I/O
        on the front panel.

        The scaled output can be selected to be current, potential,
        command potential, command current, auxiliary potential, auxiliary current

        Parameters
        ----------
        I1, I2 : current output
        output1, output2 : scaled output (can be various signals)
        Ic1, Ic2 : I-clamp command
        Vc : V-clamp command
        '''
        self.board = theboard
        self.I1 = I1  # In fact we don't use these connections for the moment.
        self.I2 = I2
        self.output1 = output1
        self.output2 = output2
        self.Ic1 = Ic1
        self.Ic2 = Ic2
        self.Vc = Vc

        self.board.gain[Ic1] = self.gain['Ic1']
        self.board.gain[Ic2] = self.gain['Ic2']
        self.board.gain[Vc] = self.gain['Vc']

    def acquire(self, *inputs, **outputs):
        '''
        Send commands and acquire signals.

        Parameters
        ----------
        inputs
            A list of input variables to acquire. From: V1, V2, I1, I2
            A maximum of two inputs.
        outputs
            A dictionary of commands. From: I1, I2, V, V1. (if V: TEVC; if V1: SEVC)
        '''
        if len(inputs) > 2:
            raise IndexError("Not more than two signals can be measured.")
        if len(outputs) > 2:
            raise IndexError('No more than two command signals can be passed.')

        # Set the mode and gains depending on outputs
        board_outputs = dict()
        for name in outputs.keys():
            if name=='I1': # current clamp on first channel
                board_outputs['Ic1'] = outputs['I1']
                if (self.current_mode[FIRST_CHANNEL] != MODE_ICLAMP) and \
                   (self.current_mode[FIRST_CHANNEL] != MODE_DCC):
                    self.current_clamp(FIRST_CHANNEL) # alternatively, we could raise an error
            elif name=='I2': # current clamp on first channel
                board_outputs['Ic2'] = outputs['I2']
                if (self.current_mode[SECOND_CHANNEL] != MODE_ICLAMP) and \
                   (self.current_mode[SECOND_CHANNEL] != MODE_HVIC):
                    self.current_clamp(SECOND_CHANNEL) # alternatively, we could raise an error
            elif name=='V1': # dSEVC
                board_outputs['Vc'] = outputs['Vc']
                if (self.current_mode[FIRST_CHANNEL] != MODE_DSEVC):
                    self.dSEVC()
            elif name=='V': # TEVC
                board_outputs['Vc'] = outputs['Vc']
                if (self.current_mode[FIRST_CHANNEL] != MODE_TEVC):
                    self.TEVC()
            else:
                raise IndexError('Unrecognized output name {}'.format(name))

        # Set the signals depending on inputs
        # There are possibilities not implemented here
        board_inputs = []
        for channel,name in enumerate(inputs):
            board_inputs.append('output{}'.format(channel+1))
            output_name = [self.output1, self.output2][channel]
            if name == 'V1':
                self.set_scaled_output_signal(SIGNAL_ID_10V1, channel)
                self.board.gain[output_name] = self.gain['V'] # should be updated with actual gain
            elif name == 'V2':
                self.set_scaled_output_signal(SIGNAL_ID_10V2, channel)
                self.board.gain[output_name] = self.gain['V'] # should be updated with actual gain
            elif name == 'I1':
                self.set_scaled_output_signal(SIGNAL_ID_I1, channel)
                self.board.gain[output_name] = self.gain['I'] # should be updated with actual gain
            elif name == 'I2':
                self.set_scaled_output_signal(SIGNAL_ID_I2, channel)
                self.board.gain[output_name] = self.gain['I'] # should be updated with actual gain
            else:
                raise IndexError('Unrecognized input name {}'.format(name))

        # Set gains
        """
        gain = self.get_scaled_output_signal_gain(FIRST_CHANNEL)
        self.board.gain[self.output1] = gain  # or 1/gain?
        print("Gain of first channel = {}".format(gain))
        gain = self.get_scaled_output_signal_gain(SECOND_CHANNEL)
        self.board.gain[self.output2] = gain  # or 1/gain?
        print("Gain of second channel = {}".format(gain))
        """

        # print(self.board.gain)

        return self.board.acquire(*board_inputs, **board_outputs)


    def check_error(self, fail=False):
        """
        Check the error code of the last command.

        Parameters
        ----------
        fail : bool
            If ``False`` (the default), any error will give rise to a warning;
            if ``True``, any error will give rise to an `IOError`.
        """
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
        """
        Find and select the amplifier.
        """
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

        # What's this?
        if not self.dll.AXC_SetSyncOutput(self.msg_handler,
                                          ctypes.c_int(AMPLIFIER_MODE),
                                          ctypes.byref(self.last_error)):
            self.check_error()

    # **** Headstages ****

    # Get headstage feedback resistor value Rf in ohm
    def get_Rf(self, channel):
        Rf = ctypes.c_double(0.)
        if not self.dll.AXC_GetRf(self.msg_handler,ctypes.byref(Rf),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_bool(False), # 'auxiliary"
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return Rf.value

    # **** Scaled output ****

    def set_scaled_output_signal(self, signal, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(channel),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()

    # **** Gains ****

    # Gains are relative to the standard gain (1 to 1000)
    # There are only a restricted number of allowed gains, the amplifier rounds up automatically
    def set_scaled_output_signal_gain(self, gain, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputGain(self.msg_handler,
                                                ctypes.c_double(gain),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_signal_gain(self, channel, mode=None):
        gain = ctypes.c_double(0.)
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_GetScaledOutputGain(self.msg_handler,
                                                ctypes.byref(gain),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()
        return gain.value

    # **** Modes ****

    def current_clamp(self, channel):
        self.current_mode[channel] = MODE_ICLAMP
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(channel),
                                    ctypes.c_uint(MODE_ICLAMP),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def DCC(self):
        # DCC only allowed on the first channel
        self.current_mode[FIRST_CHANNEL] = MODE_DCC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(FIRST_CHANNEL),
                                    ctypes.c_uint(MODE_DCC),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def dSEVC(self):
        # dSEVC only allowed on the first channel
        self.current_mode[FIRST_CHANNEL] = MODE_DSEVC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(FIRST_CHANNEL),
                                    ctypes.c_uint(MODE_DSEVC),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def HVIC(self):
        # High voltage current clamp, only on second channel
        self.current_mode[SECOND_CHANNEL] = MODE_HVIC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(SECOND_CHANNEL),
                                    ctypes.c_uint(MODE_HVIC),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def TEVC(self):
        # Two electrode voltage clamp, only on second channel
        self.current_mode[FIRST_CHANNEL] = MODE_IZERO
        self.current_mode[SECOND_CHANNEL] = MODE_TEVC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(SECOND_CHANNEL),
                                    ctypes.c_uint(MODE_TEVC),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def I0(self, channel):
        # I = 0
        self.current_mode[channel] = MODE_IZERO
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(channel),
                                    ctypes.c_uint(MODE_IZERO),
                                    ctypes.byref(self.last_error)):
            self.check_error()

    def switch_holding(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetHoldingEnable(self.msg_handler,
                                             ctypes.c_bool(enable),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def set_holding(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetHoldingLevel(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    # **** Pipette offset ****

    def auto_pipette_offset(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_AutoPipetteOffset(self.msg_handler,
                                              ctypes.c_uint(channel),
                                              ctypes.c_uint(mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    def get_pipette_offset(self, channel, mode = None):
        # Probably in volt
        if mode is None:
            mode = self.current_mode[channel]
        offset = ctypes.c_double(0.)
        if not self.dll.AXC_GetPipetteOffset(self.msg_handler,
                                              ctypes.byref(offset),
                                              ctypes.c_uint(channel),
                                              ctypes.c_uint(mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        return offset.value

    # **** Bridge balance ****
    def set_bridge_balance_lock(self, state, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetBridgeLock(self.msg_handler,
                                            ctypes.c_bool(False),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    ## This only enables bridge balance and capa comp
    def set_bridge_balance(self, state, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetBridgeEnable(self.msg_handler,
                                            ctypes.c_bool(state),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        '''
        if not self.dll.AXC_SetCapNeutEnable(self.msg_handler,
                                            ctypes.c_bool(state),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        '''

    def set_bridge_resistance(self, resistance, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        self.set_bridge_balance_lock(False, channel, mode)
        if not self.dll.AXC_SetBridgeLevel(self.msg_handler,
                                           ctypes.c_double(resistance),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()

    def get_bridge_resistance(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        resistance = ctypes.c_double(0.)
        if not self.dll.AXC_GetBridgeLevel(self.msg_handler,
                                           ctypes.byref(resistance),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()
        return resistance.value

    # This one doesn't work: sets the resistance to 0
    def auto_bridge_balance(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        self.set_bridge_balance_lock(False, channel, mode)
        if not self.dll.AXC_AutoBridge(self.msg_handler,
                                       ctypes.c_uint(channel),
                                       ctypes.c_uint(mode),
                                       ctypes.byref(self.last_error)):
            self.check_error()
        return self.get_bridge_resistance(channel)

    ##### Zap functions, made up (this is not good)
    def zap(self, channel, mode): #No built-in zap function
        if mode is None:
            mode = self.current_mode[channel]
        zap_amplitude = 1.
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(zap_amplitude),
                                              ctypes.c_uint(channel),
                                              ctypes.c_uint(mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_Pulse(self.msg_handler,
                                  ctypes.c_uint(channel),
                                  ctypes.c_uint(mode),
                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_zap_duration(self, duration, channel, mode):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPulseDuration(self.msg_handler,
                                             ctypes.c_double(duration),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
            print("Set Pulse Duration")

    def get_meter_value(self, channel):
        value = ctypes.c_double(0.)
        auxiliary = False
        if not self.dll.AXC_GetRf(self.msg_handler,
                                  ctypes.byref(value),
                                  ctypes.c_uint(channel),
                                  ctypes.c_bool(auxiliary),
                                  ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def switch_resistance_meter(self, enable, channel):
        custom_set_Rf = 1.0e+8
        custom_set_Ci = 10.0e-12
        if not self.dll.AXC_SetCustomHeadstageValues(self.msg_handler,
                                                     ctypes.c_double(custom_set_Rf),
                                                     ctypes.c_double(custom_set_Ci),
                                                     ctypes.c_bool(enable),
                                                     ctypes.c_uint(channel),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    def switch_pulses(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTestSignalEnable(self.msg_handler,
                                                ctypes.c_bool(enable),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    def set_pulses_amplitude(self, amplitude, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                              ctypes.c_double(amplitude),
                                              ctypes.c_uint(channel),
                                              ctypes.c_uint(mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    def set_pulses_frequency(self, frequency, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTestSignalFrequency(self.msg_handler,
                                                   ctypes.c_double(frequency),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

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
    dt = 0.1 * ms

    board = NI()
    board.sampling_rate = float(10000.)
    board.set_analog_input('output1', channel=0)
    board.set_analog_input('I1', channel=1)
    board.set_analog_output('Ic1', channel=1)

    amp = AxoClamp900A()
    amp.configure_board(board, output1="output1", I1='I1', Ic1='IC1')

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

