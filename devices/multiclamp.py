"""
Basic Interface to the MultiClamp 700A and 700B amplifiers.

Note that the MultiClamp Commander has to be running in order to use the device.
"""
import ctypes
import functools
import os
import logging
import time

NO_ERROR = 6000


def needs_select(func):
    """
    Decorator for all methods of `MultiClamp` that need to select the device
    first (only calls `Multiclamp.select_amplifier` if the respective device is
    not already the selected device).
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwds):
        if not MultiClamp.selected_device == self:
            self.select_amplifier()
        return func(self, *args, **kwds)
    return wrapper


def _identify_amplifier(model, serial, port, device, channel):
    """
    Return a dictionary with the identifying information for a MultiClamp
    device, based on the values filled in by ``MCCMSG_FindFirstMultiClamp``/
    ``MCCMSG_FindNextMultiClamp``. For a 700A device, returns the port, the
    device number and the channel; for a 700B device, returns the serial number
    and the channel. In all cases, the dictionary contains the `model` key with
    `700A` or `700B` as a value.
    """
    if model.value == 0:  # 700A
        logging.info(('Found a MultiClamp 700A (Port: {}, Device: {}, '
                      'Channel: {})').format(port.value, device.value,
                                             channel.value))
        return {'model': '700A', 'port': port.value, 'device': device.value,
                'channel': channel.value}
    elif model.value == 1:  # 700B
        logging.info(('Found a MultiClamp 700B (Serial number: {}, '
                      'Channel: {})').format(serial.value, channel.value))
        return {'model': '700B', 'serial': serial.value,
                'channel': channel.value}
    else:
        raise AssertionError('Unknown model')


class MultiClamp(object):
    """
    Device representing a MultiClamp amplifer channel (i.e., one amplifier with
    two channels is represented by two devices).
    
    Parameters
    ----------
    kwds
        Enough information to uniquely identify the device. If there is a single
        device, no information is needed. If there is a single amplifier with
        two channels, only the channel number (e.g. ``channel=1``) is needed.
        If there are multiple amplifiers, they can be identified via their port/
        device number (700A) or using their serial number (700B).
    """
    # The path where ``AxMultiClampMsg.dll`` is located
    dll_path = r'C:\Program Files\Molecular Devices\MultiClamp 700B Commander\3rd Party Support\AxMultiClampMsg'
    # A list of all present devices
    all_devices = None
    # The currently selected device
    selected_device = None

    def __init__(self, **kwds):
        self.dll = ctypes.WinDLL(os.path.join(MultiClamp.dll_path,
                                              'AxMultiClampMsg.dll'))
        self.last_error = ctypes.c_int(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.msg_handler = self.dll.MCCMSG_CreateObject(ctypes.byref(self.last_error))
        self.check_error(fail=True)
        if MultiClamp.all_devices is None:
            MultiClamp.all_devices = self.find_amplifiers()
        self.identification = kwds
        self.select_amplifier()

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
            # Get the error text
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           self.error_msg,
                                           ctypes.c_uint(256))
            full_error = ('An error occurred while communicating with the '
                          'MultiClamp amplifier: {}'.format(self.error_msg.value))
            if fail:
                raise IOError(full_error)
            else:
                logging.warn(full_error)
            # Reset the error code
            self.last_error.value = NO_ERROR

    def find_amplifiers(self):
        """
        Return a list of all amplifier devices (each described by a dictionary,
        see `_identifiy_amplifier`).
        
        Returns
        -------
        amplifiers : list of dict
            A list of all detected amplifier devices.
        """
        model = ctypes.c_uint()
        port = ctypes.c_uint()
        device = ctypes.c_uint()
        channel = ctypes.c_uint()
        serial = ctypes.create_string_buffer(16)
        devices = []
        if self.dll.MCCMSG_FindFirstMultiClamp(self.msg_handler,
                                               ctypes.byref(model),
                                               serial,
                                               ctypes.c_uint(16),  # buffer size
                                               ctypes.byref(port),
                                               ctypes.byref(device),
                                               ctypes.byref(channel),
                                               ctypes.byref(self.last_error)):
            devices.append(_identify_amplifier(model, serial, port, device,
                                               channel))
        else:
            self.check_error()
        while self.dll.MCCMSG_FindNextMultiClamp(self.msg_handler,
                                                 ctypes.byref(model),
                                                 serial,
                                                 ctypes.c_uint(16),  # buffer size
                                                 ctypes.byref(port),
                                                 ctypes.byref(device),
                                                 ctypes.byref(channel),
                                                 ctypes.byref(self.last_error)):
            devices.append(_identify_amplifier(model, serial, port, device,
                                               channel))
        return devices

    def select_amplifier(self):
        """
        Select the current amplifier (will be called automatically when
        executing command such as `MultiClamp.voltage_clamp`.
        """
        multiclamps = []
        for multiclamp in MultiClamp.all_devices:
            if all(multiclamp.get(key, None) == value
                   for key, value in self.identification.iteritems()):
                multiclamps.append(multiclamp)
        if len(multiclamps) == 0:
            raise RuntimeError('No device identified via {} found'.format(self.identification))
        elif len(multiclamps) > 1:
            raise RuntimeError('{} devices identified via {} found'.format(len(multiclamps),
                                                                           self.identification))
        multiclamp = multiclamps[0]
        if multiclamp['model'] == '700A':
            model = ctypes.c_uint(0)
            serial = None
            port = ctypes.c_uint(multiclamp['port'])
            device = ctypes.c_uint(multiclamp['device'])
            channel = ctypes.c_uint(multiclamp['channel'])
        elif multiclamp['model'] == '700B':
            model = ctypes.c_uint(1)
            serial = multiclamp['serial']
            port = None
            device = None
            channel = ctypes.c_uint(multiclamp['channel'])

        if not self.dll.MCCMSG_SelectMultiClamp(self.msg_handler,
                                                model,
                                                serial,
                                                port,
                                                device,
                                                channel,
                                                ctypes.byref(self.last_error)):
            self.check_error(fail=True)
        MultiClamp.selected_device = self

    @needs_select
    def voltage_clamp(self):
        # MCCMSG_MODE_VCLAMP = 0
        if not self.dll.MCCMSG_SetMode(self.msg_handler, ctypes.c_uint(0),
                                       ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def current_clamp(self):
        # MCCMSG_MODE_ICLAMP = 1
        if not self.dll.MCCMSG_SetMode(self.msg_handler, ctypes.c_uint(1),
                                       ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_fast_compensation_capacitance(self):
        capacitance = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetFastCompCap(self.msg_handler,
                                              ctypes.byref(capacitance),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        return capacitance

    @needs_select
    def set_fast_compensation_capacitance(self, capacitance):
        if not self.dll.MCCMSG_SetFastCompCap(self.msg_handler,
                                              ctypes.c_double(capacitance),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def auto_fast_compensation(self):
        if not self.dll.MCCMSG_AutoFastComp(self.msg_handler,
                                            ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_slow_compensation_capacitance(self):
        capacitance = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetSlowCompCap(self.msg_handler,
                                              ctypes.byref(capacitance),
                                              ctypes.byref(self.last_error)):
            self.check_error()
        return capacitance

    @needs_select
    def set_slow_compensation_capacitance(self, capacitance):
        if not self.dll.MCCMSG_SetSlowCompCap(self.msg_handler,
                                              ctypes.c_double(capacitance),
                                              ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def auto_slow_compensation(self):
        if not self.dll.MCCMSG_AutoSlowComp(self.msg_handler,
                                            ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def pulse(self):
        if not self.dll.MCCMSG_Pulse(self.msg_handler,
                                     ctypes.byref(self.last_error)):

            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_pulse_amplitude(self, amplitude):
        if not self.dll.MCCMSG_SetPulseAmplitude(self.msg_handler,
                                                 ctypes.c_double(amplitude),
                                                 ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_pulse_amplitude(self):
        amplitude = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetPulseAmplitude(self.msg_handler,
                                                 ctypes.byref(amplitude),
                                                 ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return amplitude

    @needs_select
    def set_pulse_duration(self, duration):
        if not self.dll.MCCMSG_SetPulseDuration(self.msg_handler,
                                                ctypes.c_double(duration),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_pulse_duration(self):
        duration = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetPulseDuration(self.msg_handler,
                                                ctypes.byref(duration),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return duration

    @needs_select
    def freq_pulse_enable(self, enable):
        if not self.dll.MCCMSG_SetTestSignalEnable(self.msg_handler,
                                                   ctypes.c_bool(enable),
                                                   ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_freq_pulse_amplitude(self, amplitude):
        if not self.dll.MCCMSG_SetTestSignalAmplitude(self.msg_handler,
                                                      ctypes.c_double(amplitude),
                                                      ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_freq_pulse_amplitude(self):
        amplitude = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetTestSignalAmplitude(self.msg_handler,
                                                      ctypes.byref(amplitude),
                                                      ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return amplitude

    @needs_select
    def set_freq_pulse_frequency(self, frequency):
        if not self.dll.MCCMSG_SetTestSignalFrequency(self.msg_handler,
                                                      ctypes.c_double(frequency),
                                                      ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_freq_pulse_frequency(self):
        frequency = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetTestSignalFrequency(self.msg_handler,
                                                      ctypes.byref(frequency),
                                                      ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return frequency

    @needs_select
    def meter_resist_enable(self, enable):
        if not self.dll.MCCMSG_SetMeterResistEnable(self.msg_handler,
                                                    ctypes.c_bool(enable),
                                                    ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_meter_resist_enable(self):
        enable = ctypes.c_bool(False)
        if not self.dll.MCCMSG_GetMeterResistEnable(self.msg_handler,
                                                    ctypes.byref(enable),
                                                    ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return enable

    @needs_select
    def set_leak_comp_enable(self, enable):
        if not self.dll.MCCMSG_SetLeakSubEnable(self.msg_handler,
                                                ctypes.c_bool(enable),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_leak_res(self):
        res = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetLeakSubResist(self.msg_handler,
                                                ctypes.byref(res),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return res

    @needs_select
    def auto_leak_res(self):
        if not self.dll.MCCMSG_AutoLeakSub(self.msg_handler,
                                           ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_primary_signal_membcur(self):
        if not self.dll.MCCMSG_SetPrimarySignal(self.msg_handler,
                                                ctypes.c_uint(0),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_primary_signal_membcur(self):
        res = ctypes.c_uint(0)
        if not self.dll.MCCMSG_GetPrimarySignal(self.msg_handler,
                                                ctypes.byref(res),
                                                ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return res

    @needs_select
    def set_primary_signal_gain(self, gain):
        if not self.dll.MCCMSG_SetPrimarySignalGain(self.msg_handler,
                                                    ctypes.c_double(gain),
                                                    ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_primary_signal_lpf(self, lpf):
        if not self.dll.MCCMSG_SetPrimarySignalLPF(self.msg_handler,
                                                   ctypes.c_double(lpf),
                                                   ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_primary_signal_hpf(self, hpf):
        if not self.dll.MCCMSG_SetPrimarySignalHPF(self.msg_handler,
                                                   ctypes.c_double(hpf),
                                                   ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_secondary_signal_membpot(self):
        if not self.dll.MCCMSG_SetSecondarySignal(self.msg_handler,
                                                  ctypes.c_uint(1),
                                                  ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_secondary_signal_membpot(self):
        res = ctypes.c_uint(0)
        if not self.dll.MCCMSG_GetSecondarySignal(self.msg_handler,
                                                  ctypes.byref(res),
                                                  ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return res

    @needs_select
    def set_secondary_signal_lpf(self, lpf):
        if not self.dll.MCCMSG_SetSecondarySignalLPF(self.msg_handler,
                                                     ctypes.c_double(lpf),
                                                     ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def set_secondary_signal_gain(self, gain):
        if not self.dll.MCCMSG_SetSecondarySignalGain(self.msg_handler,
                                                      ctypes.c_double(gain),
                                                      ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def auto_pipette_offset(self):
        if not self.dll.MCCMSG_AutoPipetteOffset(self.msg_handler,
                                                 ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)

    @needs_select
    def get_meter_value(self):
        value = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetMeterValue(self.msg_handler,
                                             ctypes.byref(value),
                                             ctypes.c_uint(0),
                                             ctypes.byref(self.last_error)):
            sz_error = ctypes.c_char_p()
            self.dll.MCCMSG_BuildErrorText(self.msg_handler,
                                           self.last_error,
                                           sz_error,
                                           ctypes.sizeof(sz_error))
            self.dll.AfxMessageBox(sz_error, self.dll.MB_ICONSTOP)
        return value

    def close(self):
        self.dll.MCCMSG_DestroyObject(self.msg_handler)
        self.msg_handler = None


if __name__ == '__main__':
    from math import fabs
    from matplotlib.pyplot import *

    val = []
    print('Connecting to the MultiClamp amplifier')
    mcc = MultiClamp(channel=1)
    print('Switching to voltage clamp')
    mcc.voltage_clamp()
    print('Setting compensation values')
    mcc.set_slow_compensation_capacitance(1e-12)
    mcc.set_fast_compensation_capacitance(5e-12)
    print('Compensation values:')
    print('Slow: {}'.format(mcc.get_slow_compensation_capacitance()))
    print('Fast: {}'.format(mcc.get_fast_compensation_capacitance()))
    print('Running automatic slow compensation')
    mcc.auto_slow_compensation()
    print('Running automatic fast compensation')
    mcc.auto_fast_compensation()
    print('Compensation values:')
    print('Slow: {}'.format(mcc.get_slow_compensation_capacitance()))
    print('Fast: {}'.format(mcc.get_fast_compensation_capacitance()))
    mcc.set_freq_pulse_amplitude(1e-2)
    mcc.set_freq_pulse_frequency(1e-3)
    mcc.set_pulse_amplitude(1e-2)
    mcc.set_pulse_duration(1e-2)
    mcc.set_primary_signal_membcur()
    mcc.set_primary_signal_lpf(2000)
    mcc.set_secondary_signal_membpot()
    mcc.set_secondary_signal_lpf(2000)
    time.sleep(.5)
    mcc.auto_pipette_offset()
    mcc.meter_resist_enable(True)
    time.sleep(3)
    mcc.freq_pulse_enable(True)
    init = time.time()
    while time.time() - init < 1:
        val += [mcc.get_meter_value().value]
    #print time.time()*1000 - init
    print min(val)
    print max(val)
    print np.median(val)
    plot(val)
    mcc.meter_resist_enable(False)
    mcc.freq_pulse_enable(False)
    mcc.meter_resist_enable(False)
    mcc.close()
    show()
