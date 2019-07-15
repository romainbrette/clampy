# -*- coding: utf-8 -*-
"""
Basic Interface to the Axoclamp 900A amplifier.

Note that the AxoClamp Commander should *not* be running in order to use the device.
(installed version: 1.2)
Download page:
http://mdc.custhelp.com/app/answers/detail/a_id/18959/~/axon%E2%84%A2-axoclamp%E2%84%A2-download-page

Gains according to the manual:
I-Clamp, DCC: 1, 10, or 100 nA/V (depends on headstage)
HVIC : 10, 100, or 1000 nA/V (depends on headstage).
dSEVC : 20 mV/V
dSEVC AC voltage‐clamp gain:   0.003–30 nA/mV, 0.03–300 nA/mV, 0.3–3000 nA/mV (depends on headstage).
TEVC : 20 mV/V

In the manual: "Regarding third‐party software, see our webpage “Developer Info”
for a detailed Software Development Kit that describes how to read telegraph information."

p44 of the manual: "Auto Bridge Balance works only in the bath."
p115: "Bridge Balance is available only in I‐Clamp mode, when Membrane Potential is
selected as the Scaled Output signal.
For the Bridge Balance algorithm to work correctly, always use Pipette Capacitance Neutralization first."
>> So I think the solution might be to select the scaled output signal first (done).

TODO:
* Try GetPropertyRules() to see what is accessible
  AXC_SetHardwareAccessEnable
* We should be able to set all the gains (maybe with the table` directly)
* Use names for channels as on the amplifier panel
"""
import ctypes
import logging
import numpy as np
import os
from ctypes.wintypes import LPCSTR
from time import sleep

__all__ = ['AxoClamp900A', 'SIGNAL_ID_10V1','SIGNAL_ID_10V2', 'SIGNAL_ID_I1', 'SIGNAL_ID_I2', 'SIGNAL_ID_DIV10I2']

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

# Oscillation killer methods
OSCKILLER_METHOD_DISABLE   = 0
OSCKILLER_METHOD_REDUCE    = 1

class AXC_PropertyRules(ctypes.Structure):
    _fields_ = [
        ("bMode", ctypes.c_bool),
        ("bAutoEnable", ctypes.c_bool),
        ("bAutoPolarity", ctypes.c_bool),
        ("bAutoSource", ctypes.c_bool),
        ("bAutoThreshold", ctypes.c_bool),
        ("bAutoICReturn", ctypes.c_bool),
        ("bAutoICDelay", ctypes.c_bool),
        ("bAutoVCDelay", ctypes.c_bool),
        ("bHoldingEnable", ctypes.c_bool),
        ("bHoldingLevel", ctypes.c_bool),
        ("bExtCmdEnable", ctypes.c_bool),
        ("bTestSignalEnable", ctypes.c_bool),
        ("bTestSignalAmplitude", ctypes.c_bool),
        ("bTestSignalFrequency", ctypes.c_bool),
        ("bPulse", ctypes.c_bool),
        ("bPulseDuration", ctypes.c_bool),
        ("bPulseAmplitude", ctypes.c_bool),
        ("bBuzz", ctypes.c_bool),
        ("bBuzzDuration", ctypes.c_bool),
        ("bBuzzAmplitude", ctypes.c_bool),
        ("bAutoPipetteOffset", ctypes.c_bool),
        ("bPipetteOffsetLock", ctypes.c_bool),
        ("bPipetteOffset", ctypes.c_bool),
        ("bOscKillerEnable", ctypes.c_bool),
        ("bOscKillerMethod", ctypes.c_bool),
        ("bAutoBridge", ctypes.c_bool),
        ("bBridgeLock", ctypes.c_bool),
        ("bBridgeEnable", ctypes.c_bool),
        ("bBridgeLevel", ctypes.c_bool),
        ("bClearElectrode", ctypes.c_bool),
        ("bCapNeutEnable", ctypes.c_bool),
        ("bCapNeutLevel", ctypes.c_bool),
        ("bTrackEnable", ctypes.c_bool),
        ("bTrackLevel", ctypes.c_bool),
        ("bTrackSpeed", ctypes.c_bool),
        ("bScaledOutputSignal", ctypes.c_bool),
        ("bScaledOutputSignalGain", ctypes.c_bool),
        ("bScaledOutputSignalLPF", ctypes.c_bool),
        ("bScaledOutputSignalLPFType", ctypes.c_bool),
        ("bScaledOutputSignalHPF", ctypes.c_bool),
        ("bAutoScaledOutputZero", ctypes.c_bool),
        ("bScaledOutputZeroEnable", ctypes.c_bool),
        ("bScaledOutputZeroLevel", ctypes.c_bool),
        ("bSamplePeriod", ctypes.c_bool),
        ("bLoopGain", ctypes.c_bool),
        ("bLoopLag", ctypes.c_bool),
        ("bDCRestoreEnable", ctypes.c_bool),
        ("bAudioSignal", ctypes.c_bool),
    ]

class AXC_MeterData(ctypes.Structure):
    _fields_ = [
        ("dMeter1", ctypes.c_double),
        ("dMeter2", ctypes.c_double),
        ("dMeter3", ctypes.c_double),
        ("dMeter4", ctypes.c_double),
        ("bOvldMeter1", ctypes.c_bool),
        ("bOvldMeter2", ctypes.c_bool),
        ("bOvldMeter3", ctypes.c_bool),
        ("bOvldMeter4", ctypes.c_bool),

        ("bPowerFail", ctypes.c_bool),
        ("bPresenceChan1", ctypes.c_bool),
        ("bPresenceChan2", ctypes.c_bool),
        ("bPresenceAux1", ctypes.c_bool),
        ("bPresenceAux2", ctypes.c_bool),
        ("bIsVClampChan1", ctypes.c_bool),
        ("bIsVClampChan2", ctypes.c_bool),
        ("bOscKillerChan1", ctypes.c_bool),
        ("bOscKillerChan2", ctypes.c_bool),
    ]

class AXC_PropertyRange(ctypes.Structure):
    _fields_ = [
        ("dValMin", ctypes.c_double),
        ("dValMax", ctypes.c_double),
        ("nValMin", ctypes.c_int),
        ("nValMax", ctypes.c_int),
    ]

class AXC_Signal(ctypes.Structure):
    _fields_ = [
        ("uChannel", ctypes.c_uint),
        ("uID", ctypes.c_uint),
        ("pszName", LPCSTR),
        ("bValid", ctypes.c_bool),
    ]

class AXC_SignalSettings(ctypes.Structure):
    _fields_ = [
        ("bSave", ctypes.c_bool),
        ("dGain", ctypes.c_double),
        ("dLPF", ctypes.c_double),
        ("dHPF", ctypes.c_double),
        ("dZeroLevel", ctypes.c_double),
        ("bZeroEnable", ctypes.c_bool),
        ("uLPFType", ctypes.c_uint),
    ]

def _identify_amplifier(model, serial):
    if model.value == 0:  # 900A
        logging.info(('Found an AxoClamp 900A (Serial: {}').format(serial.value))
        return {'model': '900A', 'serial': serial.value}
    else:
        raise AssertionError('Unknown model')


class AxoClamp900A(object):
    """
    Device representing an Axoclamp 900A amplifier, which has two channels.
    """
    dll_path = r'C:\Program Files (x86)\Molecular Devices\AxoClamp 900A Commander 1.2' # We need something more robust!
    #dll_path = r'C:\Program Files (x86)\Molecular Devices\AxoClamp 900A Commander' # We need something more robust!

    def __init__(self, **kwds):
        #self.dllHID = ctypes.WinDLL(os.path.join(AxoClamp900A.dll_path, 'AxHIDManager.dll'))
        self.dll = ctypes.WinDLL(os.path.join(AxoClamp900A.dll_path, 'AxoclampDriver.dll'))
        self.last_error = ctypes.c_uint(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.is_open = ctypes.c_bool(False)
        self.first_headstage_connect = ctypes.c_bool(False)
        self.second_headstage_connect = ctypes.c_bool(False)
        self.first_headstage_type = ctypes.c_uint(20)
        self.second_headstage_type = ctypes.c_uint(20)
        self.current_mode = [0,0]
        self.check_error(fail=True)
        self.select_amplifier()
        #self.save_folder = 'C:\Users\Hoang Nguyen\Documents\Molecular Devices\Axoclamp 900A Commander'

        volt = 1.
        mV = 1e-3
        nA = 1e-9

        self.gain = {'V-CLAMP': 1./(20 * mV / volt)}

        # Sets gains according to headstage Rf
        multiplier = self.get_Rf(FIRST_CHANNEL)/1e6
        #print('Rf on first channel: {}'.format(multiplier))
        self.gain['I-CLAMP 1'] = multiplier * 0.01*volt/nA
        multiplier = self.get_Rf(SECOND_CHANNEL)/1e6
        #print('Rf on second channel: {}'.format(multiplier))
        self.gain['I-CLAMP 2'] = multiplier * 0.01*volt/nA
        # HVIC gain not set here

        # Output gains
        self.gain['V'] = 10*mV/mV
        self.gain['I'] = 0.1*volt/nA

    def configure_scaled_outputs(self, board, scaled_output1=None, scaled_output2=None):
        '''
        Configures the virtual channels of the board for the two scaled outputs

        Arguments
        ---------
        board : the board
        scaled_output1 : name of the board channel connected to SCALED OUTPUT 1
        scaled_output2 : name of the board channel connected to SCALED OUTPUT 2
        '''
        names = ['XICMD1','ICMD1','10V1','I1','MON','RMP','XICMD2','ICMD2',
                 '10V2','I2','DIV10V2','DIV10I2','XVCMD','VCMD','10AUX1','10AUX2',
                 '10mV','GND']
        for name, ID in zip(names, range(18)):
            board.set_virtual_input(name, channel=(scaled_output1, scaled_output2), deviceID=ID,
                                    select=self.set_scaled_output_signal)

    def get_scaled_signal_gain(self, signal):
        '''
        Returns the gain of the named scaled signal
        '''
        if signal in [SIGNAL_ID_10V1, SIGNAL_ID_10V2]:
            return self.gain['V']  # could be simplified with a general table
        elif signal in [SIGNAL_ID_I1, SIGNAL_ID_I2]:
            return self.gain['I']
        elif signal == SIGNAL_ID_DIV10I2:
            return self.gain['I'] / 10.

    def get_gain(self, name):
        '''
        Returns the gain of the named channel
        '''
        if name=='SCALED OUTPUT 1':
            signal = self.get_scaled_output_signal(0)
            gain=self.get_scaled_signal_gain(signal) * self.get_scaled_output_signal_gain(0) # or divided?
            if gain==0.: # not set before: we set it to 1
                self.set_scaled_output_signal_gain(1,0)
                gain=1.
        elif name=='SCALED OUTPUT 2':
            signal = self.get_scaled_output_signal(1)
            gain=self.get_scaled_signal_gain(signal) * self.get_scaled_output_signal_gain(1)
            if gain==0.: # not set before: we set it to 1
                self.set_scaled_output_signal_gain(1,1)
                gain=1.
        else:
            gain=self.gain[name]
        return gain

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
            # 3 trials
            error = False
            for _ in range(3):
                if not self.dll.AXC_OpenDevice(self.msg_handler,
                                               serial,
                                               ctypes.c_bool(True),
                                               ctypes.byref(self.last_error)):
                    error = True
                    sleep(1)
                else:
                    error = False
                    break
            if error:
                self.check_error(True)

        # What's this?
        #if not self.dll.AXC_SetSyncOutput(self.msg_handler,
        #                                  ctypes.c_int(AMPLIFIER_MODE),
        #                                  ctypes.byref(self.last_error)):
        #    self.check_error()

    def reset(self):
        # Resets all parameters on the amplifier
        if not self.dll.AXC_Reset(self.msg_handler,
                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_cache_enable(self, enable):
        if not self.dll.AXC_SetCacheEnable(self.msg_handler,
                                           ctypes.c_bool(enable),
                                           ctypes.byref(self.last_error)):
            self.check_error()

    def get_property_rules (self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRules()
        if not self.dll.AXC_GetPropertyRules(self.msg_handler,
                                             ctypes.byref(data),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        for field_name, field_type in data._fields_:
            print field_name, getattr(data, field_name)
        return data

    # **** Headstage Functions ****

    # Get headstage feedback resistor value Rf in ohm
    def get_Rf(self, channel):
        Rf = ctypes.c_double(0.)
        if not self.dll.AXC_GetRf(self.msg_handler,ctypes.byref(Rf),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_bool(False), # 'auxiliary"
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return Rf.value

    def get_Ci(self, channel):
        Ci = ctypes.c_double(0.)
        if not self.dll.AXC_GetCi(self.msg_handler, ctypes.byref(Ci),
                                                    ctypes.c_uint(channel),
                                                    ctypes.byref(self.last_error)):
            self.check_error()
        return Ci.value

    def calibrate_headstage_properties(self, channel):
        if not self.dll.AXC_CalibrateHeadstageProperties(self.msg_handler,ctypes.c_uint(channel),
                                                                          ctypes.byref(self.last_error)):
            self.check_error()

    def headstage_connection_state(self):
        auxiliary = False
        if not self.dll.AXC_IsHeadstagePresent(self.msg_handler,
                                               ctypes.byref(self.first_headstage_connect),
                                               ctypes.c_int(FIRST_CHANNEL),
                                               ctypes.c_bool(auxiliary),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        if not self.dll.AXC_IsHeadstagePresent(self.msg_handler,
                                               ctypes.byref(self.second_headstage_connect),
                                               ctypes.c_int(SECOND_CHANNEL),
                                               ctypes.c_bool(auxiliary),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def headstage_type(self):
        auxiliary = False
        if self.first_headstage_connect:
            if not self.dll.AXC_GetHeadstageType(self.msg_handler,
                                                 ctypes.byref(self.first_headstage_connect),
                                                 ctypes.c_int(FIRST_CHANNEL),
                                                 ctypes.c_bool(auxiliary),
                                                 ctypes.byref(self.last_error)):
                self.check_error(True)
        if self.second_headstage_connect:
            if not self.dll.AXC_GetHeadstageType(self.msg_handler,
                                                 ctypes.byref(self.second_headstage_connect),
                                                 ctypes.c_int(SECOND_CHANNEL),
                                                 ctypes.c_bool(auxiliary),
                                                 ctypes.byref(self.last_error)):
                self.check_error(True)

    def switch_resistance_meter(self, enable, channel):  #set custom headstage values and enable the state
        custom_set_Rf = 1.0e+8
        custom_set_Ci = 10.0e-12
        if not self.dll.AXC_SetCustomHeadstageValues(self.msg_handler,
                                                     ctypes.c_double(custom_set_Rf),
                                                     ctypes.c_double(custom_set_Ci),
                                                     ctypes.c_bool(enable),
                                                     ctypes.c_uint(channel),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    def get_custom_headstage_values(self, enable, channel):
        set_Rf = ctypes.c_double(0.)
        set_Ci = ctypes.c_double(0.)
        if not self.dll.AXC_SetCustomHeadstageValues(self.msg_handler,
                                                     ctypes.byref(set_Rf),
                                                     ctypes.byref(set_Ci),
                                                     ctypes.c_bool(enable),
                                                     ctypes.c_uint(channel),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return (set_Rf.value, set_Ci.value)


    # **** Headstage Functions ****

    def switch_holding(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetHoldingEnable(self.msg_handler,
                                             ctypes.c_bool(enable),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def get_holding_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = False
        if not self.dll.AXC_GetHoldingEnable(self.msg_handler,
                                             ctypes.byref(enable),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_holding(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetHoldingLevel(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_holding_level(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetHoldingLevel(self.msg_handler,
                                            ctypes.byref(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_holding_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetHoldingRange(self.msg_handler,
                                            ctypes.byref(data),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** Meter and Status functions ****

    def set_meter_signal(self, meter, signal, channel, mode = None):    #channel to detect mode
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetMeterSignal(self.msg_handler,
                                               ctypes.c_uint(meter),
                                               ctypes.c_uint(signal),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_meter_signal(self, meter, channel, mode = None):    #channel to detect mode
        if mode is None:
            mode = self.current_mode[channel]
        signal = ctypes.c_uint(17)   #Ground Signal
        if not self.dll.AXC_GetHoldingLevel(self.msg_handler,
                                            ctypes.c_uint(meter),
                                            ctypes.byref(signal),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return signal

    def acquire_meter_data (self):
        data = AXC_MeterData()
        if not self.dll.AXC_AcquireMeterData(self.msg_handler,
                                             ctypes.byref(data),
                                             ctypes.byref(self.last_error)):
            self.check_error()

        for field_name, field_type in data._fields_:
            print field_name, getattr(data, field_name)
        return data

    def set_meter_attenuator(self, meter, enable):
        if not self.dll.AXC_SetMeterAttenuatorEnable(self.msg_handler,
                                                     ctypes.c_uint(meter),
                                                     ctypes.c_bool(enable),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    def get_meter_attenuator(self, meter):
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetMeterAttenuatorEnable(self.msg_handler,
                                                     ctypes.c_uint(meter),
                                                     ctypes.byref(enable),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return enable


    # **** External Command Functions ****

    def set_external_command_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetExtCmdEnable(self.msg_handler,
                                            ctypes.c_bool(enable),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_external_command_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetExtCmdEnable(self.msg_handler,
                                            ctypes.byref(enable),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def get_external_command_sensitivity(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        sensitivity = ctypes.c_double(0.)
        if not self.dll.AXC_GetExtCmdSensit(self.msg_handler,
                                            ctypes.byref(sensitivity),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return sensitivity.value


    # **** Test Signal Functions ****

    def set_test_signal_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTestSignalEnable(self.msg_handler,
                                                ctypes.c_bool(enable),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    def get_test_signal_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetTestSignalEnable(self.msg_handler,
                                                ctypes.byref(enable),
                                                ctypes.c_uint(channel),
                                                ctypes.c_uint(mode),
                                                ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_test_signal_amplitude(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTestSignalAmplitude(self.msg_handler,
                                                   ctypes.c_double(value),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    def get_test_signal_amplitude(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetTestSignalAmplitude(self.msg_handler,
                                                   ctypes.byref(value),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_test_signal_amplitude_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetTestSignalAmplitudeRange(self.msg_handler,
                                                        ctypes.byref(data),
                                                        ctypes.c_uint(channel),
                                                        ctypes.c_uint(mode),
                                                        ctypes.byref(self.last_error)):
            self.check_error()
        return data

    def set_test_signal_frequency(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTestSignalFrequency(self.msg_handler,
                                                   ctypes.c_double(value),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    def get_test_signal_frequency(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetTestSignalFrequency(self.msg_handler,
                                                   ctypes.byref(value),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_test_signal_frequency_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetTestSignalFreqRange(self.msg_handler,
                                                   ctypes.byref(data),
                                                   ctypes.byref(bufsize),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return (data, bufsize)


    # **** Pulse Functions ****

    def execute_pulse(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_Pulse(self.msg_handler,
                                  ctypes.c_uint(channel),
                                  ctypes.c_uint(mode),
                                  ctypes.byref(self.last_error)):
            self.check_error()

    def set_pulse_duration(self, value, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPulseDuration(self.msg_handler,
                                             ctypes.c_double(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def get_pulse_duration(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetPulseDuration(self.msg_handler,
                                             ctypes.byref(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_pulse_duration_table(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetPulseDuration(self.msg_handler,
                                             ctypes.byref(table),
                                             ctypes.byref(bufsize),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)

    def set_pulse_amplitude(self, value, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPulseAmplitude(self.msg_handler,
                                             ctypes.c_double(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def get_pulse_amplitude(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetPulseAmplitude(self.msg_handler,
                                             ctypes.byref(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_pulse_amplitude_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetPulseAmplitudeRange(self.msg_handler,
                                                   ctypes.byref(data),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** Buzz Functions ****
    def execute_buzz(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_Buzz(self.msg_handler,
                                 ctypes.c_uint(channel),
                                 ctypes.c_uint(mode),
                                 ctypes.byref(self.last_error)):
            self.check_error()

    def set_buzz_duration(self, value, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetBuzzDuration(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_buzz_duration(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetBuzzDuration(self.msg_handler,
                                            ctypes.byref(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_buzz_duration_table(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetBuzzDurationTable(self.msg_handler,
                                                 ctypes.byref(table),
                                                 ctypes.byref(bufsize),
                                                 ctypes.c_uint(channel),
                                                 ctypes.c_uint(mode),
                                                 ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)


    # **** Pipette Offset Functions ****

    def auto_pipette_offset(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_AutoPipetteOffset(self.msg_handler,
                                              ctypes.c_uint(channel),
                                              ctypes.c_uint(mode),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    def set_pipette_offset_lock(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPipetteOffsetLock(self.msg_handler,
                                                 ctypes.c_bool(enable),
                                                 ctypes.c_uint(channel),
                                                 ctypes.c_uint(mode),
                                                 ctypes.byref(self.last_error)):
            self.check_error()

    def get_pipette_offset_lock(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetPipetteOffsetLock(self.msg_handler,
                                                 ctypes.byref(enable),
                                                 ctypes.c_uint(channel),
                                                 ctypes.c_uint(mode),
                                                 ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_pipette_offset(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetPipetteOffset(self.msg_handler,
                                             ctypes.c_double(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def get_pipette_offset(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetPipetteOffset(self.msg_handler,
                                             ctypes.byref(value),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_pipette_offset_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetPipetteOffsetRange(self.msg_handler,
                                                  ctypes.byref(data),
                                                  ctypes.c_uint(channel),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** +/- Clear Functions ****

    def clear_electrode(self, enable, polarity, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_ClearElectrode(self.msg_handler,
                                           ctypes.c_bool(enable),
                                           ctypes.c_uint(polarity),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()


    # **** Track Functions ****

    def set_track_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTrackEnable(self.msg_handler,
                                           ctypes.c_bool(enable),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()

    def get_track_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetTrackEnable(self.msg_handler,
                                           ctypes.byref(enable),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_track_level(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTrackLevel(self.msg_handler,
                                          ctypes.c_double(value),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()

    def get_track_level(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetTrackLevel(self.msg_handler,
                                          ctypes.byref(value),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_track_level_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetTrackLevelRange(self.msg_handler,
                                               ctypes.byref(data),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return data

    def set_track_speed(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetTrackSpeed(self.msg_handler,
                                          ctypes.c_double(value),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()

    def get_track_speed(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetTrackSpeed(self.msg_handler,
                                          ctypes.byref(value),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_track_speed_table(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetTrackSpeedTable(self.msg_handler,
                                               ctypes.byref(table),
                                               ctypes.byref(bufsize),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)


    # **** Sample Rate Functions ****

    def set_sample_period(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetSamplePeriod(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_sample_period(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetSamplePeriod(self.msg_handler,
                                            ctypes.byref(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_sample_period_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetSamplePeriodRange(self.msg_handler,
                                                 ctypes.byref(data),
                                                 ctypes.c_uint(channel),
                                                 ctypes.c_uint(mode),
                                                 ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** Gain and Lag Functions ****

    def set_loop_gain(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetLoopGain(self.msg_handler,
                                        ctypes.c_double(value),
                                        ctypes.c_uint(channel),
                                        ctypes.c_uint(mode),
                                        ctypes.byref(self.last_error)):
            self.check_error()

    def get_loop_gain(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetLoopGain(self.msg_handler,
                                        ctypes.byref(value),
                                        ctypes.c_uint(channel),
                                        ctypes.c_uint(mode),
                                        ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_loop_gain_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetLoopGainRange(self.msg_handler,
                                             ctypes.byref(data),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return data

    def set_loop_lag(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetLoopLag(self.msg_handler,
                                       ctypes.c_double(value),
                                       ctypes.c_uint(channel),
                                       ctypes.c_uint(mode),
                                       ctypes.byref(self.last_error)):
            self.check_error()

    def get_loop_lag(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetLoopLag(self.msg_handler,
                                       ctypes.byref(value),
                                       ctypes.c_uint(channel),
                                       ctypes.c_uint(mode),
                                       ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_loop_lag_table(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        table = (ctypes.c_double*128)()
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetLoopLagTable(self.msg_handler,
                                            ctypes.byref(table),
                                            ctypes.byref(bufsize),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return (table, bufsize)

    def set_dc_restore_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetDCRestoreEnable(self.msg_handler,
                                               ctypes.c_bool(enable),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_dc_restore_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetDCRestoreEnable(self.msg_handler,
                                               ctypes.byref(enable),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return enable


    # **** Pipette Capacitance Neutralization Functions ****

    def set_cap_neut_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetCapNeutEnable(self.msg_handler,
                                             ctypes.c_bool(enable),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()

    def get_cap_neut_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetCapNeutEnable(self.msg_handler,
                                             ctypes.byref(enable),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_cap_neut_level(self, value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetCapNeutLevel(self.msg_handler,
                                            ctypes.c_double(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_cap_neut_level(self, channel, mode=None):
        # Apparently this is not read from the amplifier, but rather a memory of previous commands (?!)
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetCapNeutLevel(self.msg_handler,
                                            ctypes.byref(value),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_cap_neut_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetCapNeutRange(self.msg_handler,
                                             ctypes.byref(data),
                                             ctypes.c_uint(channel),
                                             ctypes.c_uint(mode),
                                             ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** oscillation Killer Functions ****

    def set_osc_killer_enable(self, enable, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetOscKillerEnable(self.msg_handler,
                                               ctypes.c_bool(enable),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_osc_killer_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetOscKillerEnable(self.msg_handler,
                                               ctypes.byref(enable),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_osc_killer_method(self, method, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetOscKillerMethod(self.msg_handler,
                                               ctypes.c_uint(method),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_osc_killer_method(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        method = ctypes.c_uint(0)   #Disable
        if not self.dll.AXC_GetCapNeutLevel(self.msg_handler,
                                            ctypes.byref(method),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return method


    # **** Bridge Balance Functions ****

    # This one doesn't work: sets the resistance to 0
    def auto_bridge_balance(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if channel == FIRST_CHANNEL: # Not sure this is what should be done
            self.set_scaled_output_signal(SIGNAL_ID_10V1, channel)
        elif channel == SECOND_CHANNEL:
            self.set_scaled_output_signal(SIGNAL_ID_10V2, channel)
        self.set_bridge_lock(False, channel, mode)
        if not self.dll.AXC_AutoBridge(self.msg_handler,
                                       ctypes.c_uint(channel),
                                       ctypes.c_uint(mode),
                                       ctypes.byref(self.last_error)):
            self.check_error()
        return self.get_bridge_resistance(channel)

    ## This only enables bridge balance and capa comp
    def set_bridge_enable(self, enable, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if channel == FIRST_CHANNEL: # Not sure this is what should be done
            self.set_scaled_output_signal(SIGNAL_ID_10V1, channel)
        elif channel == SECOND_CHANNEL:
            self.set_scaled_output_signal(SIGNAL_ID_10V2, channel)

        if not self.dll.AXC_SetBridgeEnable(self.msg_handler,
                                            ctypes.c_bool(enable),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()

    def get_bridge_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetBridgeEnable(self.msg_handler,
                                            ctypes.byref(enable),
                                            ctypes.c_uint(channel),
                                            ctypes.c_uint(mode),
                                            ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_bridge_lock(self, enable, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetBridgeLock(self.msg_handler,
                                          ctypes.c_bool(enable),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()

    def get_bridge_lock(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetBridgeLock(self.msg_handler,
                                          ctypes.byref(enable),
                                          ctypes.c_uint(channel),
                                          ctypes.c_uint(mode),
                                          ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_bridge_resistance(self, value, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        #if channel == FIRST_CHANNEL: # Not sure this is what should be done
        #    self.set_scaled_output_signal(SIGNAL_ID_10V1, channel)
        #elif channel == SECOND_CHANNEL:
        #    self.set_scaled_output_signal(SIGNAL_ID_10V2, channel)
        #self.set_bridge_lock(False, channel, mode)
        if not self.dll.AXC_SetBridgeLevel(self.msg_handler,
                                           ctypes.c_double(value),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()

    def get_bridge_resistance(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetBridgeLevel(self.msg_handler,
                                           ctypes.byref(value),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_bridge_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetBridgeRange(self.msg_handler,
                                           ctypes.byref(data),
                                           ctypes.c_uint(channel),
                                           ctypes.c_uint(mode),
                                           ctypes.byref(self.last_error)):
            self.check_error()
        return data


    # **** Scaled Output Signal Functions ****

    def set_scaled_output_signal(self, signal, channel, mode=None):
        if channel == 'SCALED OUTPUT 1':
            channel = 0
        elif channel == 'SCALED OUTPUT 2':
            channel = 1
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputSignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.c_uint(channel),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_signal(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        signal = ctypes.c_uint(17)  #Ground Signal
        if not self.dll.AXC_GetScaledOutputSignal(self.msg_handler,
                                                  ctypes.byref(signal),
                                                  ctypes.c_uint(channel),
                                                  ctypes.c_uint(mode),
                                                  ctypes.byref(self.last_error)):
            self.check_error()
        return signal.value

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

    def get_scaled_output_signal_gain_table(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetScaledOutputGainTable(self.msg_handler,
                                                     ctypes.byref(table),
                                                     ctypes.byref(bufsize),
                                                     ctypes.c_uint(channel),
                                                     ctypes.c_uint(mode),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)

    def set_scaled_output_LPFT_type(self, type, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputLPFType(self.msg_handler,
                                                   ctypes.c_uint(type),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_LPF_type(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        type = ctypes.c_uint(0)   #Disable
        if not self.dll.AXC_GetScaledOutputLPFType(self.msg_handler,
                                                   ctypes.byref(type),
                                                   ctypes.c_uint(channel),
                                                   ctypes.c_uint(mode),
                                                   ctypes.byref(self.last_error)):
            self.check_error()
        return type

    def set_scaled_output_LPF(self, lpf_value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputLPF(self.msg_handler,
                                               ctypes.c_double(lpf_value),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_LPF(self, channel, mode=None):
        lpf_value = ctypes.c_double(0.)
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_GetScaledOutputLPF(self.msg_handler,
                                               ctypes.byref(lpf_value),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return lpf_value.value

    def get_scaled_output_LPF_table(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetScaledOutputLPFTable(self.msg_handler,
                                                    ctypes.byref(table),
                                                    ctypes.byref(bufsize),
                                                    ctypes.c_uint(channel),
                                                    ctypes.c_uint(mode),
                                                    ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)

    def set_scaled_output_HPF(self, hpf_value, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputHPF(self.msg_handler,
                                               ctypes.c_double(hpf_value),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_HPF(self, channel, mode=None):
        hpf_value = ctypes.c_double(0.)
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_GetScaledOutputHPF(self.msg_handler,
                                               ctypes.byref(hpf_value),
                                               ctypes.c_uint(channel),
                                               ctypes.c_uint(mode),
                                               ctypes.byref(self.last_error)):
            self.check_error()
        return hpf_value.value

    def get_scaled_output_HPF_table(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        table = ctypes.c_double(0.)
        bufsize = ctypes.c_uint(0)
        if not self.dll.AXC_GetScaledOutputHPFTable(self.msg_handler,
                                                    ctypes.byref(table),
                                                    ctypes.byref(bufsize),
                                                    ctypes.c_uint(channel),
                                                    ctypes.c_uint(mode),
                                                    ctypes.byref(self.last_error)):
            self.check_error()
        return (table.value, bufsize)

    def auto_scaled_output_zero_offset(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_AutoScaledOutputZero(self.msg_handler,
                                                 ctypes.c_uint(channel),
                                                 ctypes.c_uint(mode),
                                                 ctypes.byref(self.last_error)):
            self.check_error()

    def set_scaled_output_zero_offset_enable(self, enable, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        if not self.dll.AXC_SetScaledOutputZeroEnable(self.msg_handler,
                                                      ctypes.c_bool(enable),
                                                      ctypes.c_uint(channel),
                                                      ctypes.c_uint(mode),
                                                      ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_zero_offset_enable(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        enable = ctypes.c_bool(False)
        if not self.dll.AXC_GetScaledOutputZeroEnable(self.msg_handler,
                                                      ctypes.byref(enable),
                                                      ctypes.c_uint(channel),
                                                      ctypes.c_uint(mode),
                                                      ctypes.byref(self.last_error)):
            self.check_error()
        return enable

    def set_scaled_output_zero_offset_level(self, value, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        self.set_bridge_lock(False, channel, mode)
        if not self.dll.AXC_SetScaledOutputZeroLevel(self.msg_handler,
                                                     ctypes.c_double(value),
                                                     ctypes.c_uint(channel),
                                                     ctypes.c_uint(mode),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    def get_scaled_output_zero_offset_level(self, channel, mode = None):
        if mode is None:
            mode = self.current_mode[channel]
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetScaledOutputZeroLevel(self.msg_handler,
                                                     ctypes.byref(value),
                                                     ctypes.c_uint(channel),
                                                     ctypes.c_uint(mode),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return value.value

    def get_scaled_output_zero_offset_range(self, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_PropertyRange()
        if not self.dll.AXC_GetScaledOutputZeroRange(self.msg_handler,
                                                     ctypes.byref(data),
                                                     ctypes.c_uint(channel),
                                                     ctypes.c_uint(mode),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return data

    def get_scaled_output_cache_settings(self, signal, channel, mode=None):
        if mode is None:
            mode = self.current_mode[channel]
        data = AXC_SignalSettings()
        if not self.dll.AXC_GetScaledOutputCacheSettings(self.msg_handler,
                                                     ctypes.byref(data),
                                                     ctypes.c_uint(signal),
                                                     ctypes.c_uint(channel),
                                                     ctypes.c_uint(mode),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return data

    def get_signal_scale_factor(self, signal):
        value = ctypes.c_double(0.)
        if not self.dll.AXC_GetSignalScaleFactor(self.msg_handler,
                                                     ctypes.byref(value),
                                                     ctypes.c_uint(signal),
                                                     ctypes.byref(self.last_error)):
            self.check_error()
        return value.value


    # # **** Serialization Functions ****
    # Do not work currently
    #
    # def save_properties(self):
    #     save_file = 'axoclamp900a'
    #     use_file = True
    #     if not self.dll.AXC_SaveProperties(self.msg_handler,
    #                                        LPCSTR(save_file),
    #                                        LPCSTR(self.save_folder),
    #                                        ctypes.c_bool(use_file),
    #                                        ctypes.byref(self.last_error)):
    #         self.check_error(fail = True)
    #
    # def load_properties(self):
    #     save_file = 'axoclamp900a'
    #     use_file = True
    #     if not self.dll.AXC_LoadProperties(self.msg_handler,
    #                                        LPCSTR(save_file),
    #                                        LPCSTR(self.save_folder),
    #                                        ctypes.c_bool(use_file),
    #                                        ctypes.byref(self.last_error)):
    #         self.check_error(fail = True)

    # **** Modes ****

    def current_clamp(self, channel):
        self.current_mode[channel] = MODE_ICLAMP
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(channel),
                                    ctypes.c_uint(MODE_ICLAMP),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        self.set_external_command_enable(True, channel)

    def DCC(self):
        # DCC only allowed on the first channel
        self.current_mode[FIRST_CHANNEL] = MODE_DCC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(FIRST_CHANNEL),
                                    ctypes.c_uint(MODE_DCC),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        self.set_external_command_enable(True, 0)

    def dSEVC(self):
        # dSEVC only allowed on the first channel
        self.current_mode[FIRST_CHANNEL] = MODE_DSEVC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(FIRST_CHANNEL),
                                    ctypes.c_uint(MODE_DSEVC),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        self.set_external_command_enable(True, 0)

    def HVIC(self):
        # High voltage current clamp, only on second channel
        self.current_mode[SECOND_CHANNEL] = MODE_HVIC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(SECOND_CHANNEL),
                                    ctypes.c_uint(MODE_HVIC),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        self.set_external_command_enable(True, 1)

    def TEVC(self):
        # Two electrode voltage clamp, only on second channel
        self.current_mode[FIRST_CHANNEL] = MODE_IZERO
        self.current_mode[SECOND_CHANNEL] = MODE_TEVC
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(SECOND_CHANNEL),
                                    ctypes.c_uint(MODE_TEVC),
                                    ctypes.byref(self.last_error)):
            self.check_error()
        self.set_external_command_enable(True, 1)

    def I0(self, channel):
        # I = 0
        self.current_mode[channel] = MODE_IZERO
        if not self.dll.AXC_SetMode(self.msg_handler,
                                    ctypes.c_uint(channel),
                                    ctypes.c_uint(MODE_IZERO),
                                    ctypes.byref(self.last_error)):
            self.check_error()

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


if __name__ == '__main__': # actually we can't run this (import error)
    from ni import *
    from pylab import *

    ms = 0.001
    pA = 1e-12
    mV = 0.001
    volt = 1
    nA = 1e-9
    dt = 0.1 * ms

    amplifier = AxoClamp900A()

    board = NI()
    board.set_analog_input('output1', channel=0, deviceID='SCALED OUTPUT 1', gain=amplifier.get_gain)
    board.set_analog_input('output2', channel=1, deviceID='SCALED OUTPUT 2', gain=amplifier.get_gain)
    board.set_analog_output('I-CLAMP 1', channel=0, deviceID='I-CLAMP 1', gain=amplifier.get_gain)
    board.set_analog_output('I-CLAMP 2', channel=1, deviceID='I-CLAMP 2', gain=amplifier.get_gain)
    board.set_analog_input('I2', channel=2, deviceID='I', gain=amplifier.get_gain)
    board.set_analog_output('V-CLAMP', channel=2, deviceID='V-CLAMP', gain=amplifier.get_gain)

    board.set_virtual_input('V1', channel=('output1', 'output2'), deviceID=SIGNAL_ID_10V1, select=amplifier.set_scaled_output_signal)
    board.set_virtual_input('V2', channel=('output1', 'output2'), deviceID=SIGNAL_ID_10V2, select=amplifier.set_scaled_output_signal)

    Ic = zeros(int(1000 * ms / dt))
    Ic[int(130 * ms / dt):int(330 * ms / dt)] += 500 * pA
    Vc = zeros(int(1000 * ms / dt))
    Vc[int(130 * ms / dt):int(330 * ms / dt)] = 20 * mV

    amplifier.current_clamp(0)

    V1, V2 = board.acquire('V1', 'V2', Ic1=Ic)

    subplot(211)
    plot(array(V1) / (mV), 'k')
    plot(array(V2) / (mV), 'r')
    subplot(212)
    plot(Ic / pA)
    show()

