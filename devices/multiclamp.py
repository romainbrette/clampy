"""
Basic Interface to the MultiClamp 700A and 700B amplifiers.

Note that the MultiClamp Commander has to be running in order to use the device.

For each of the two channels, we have:
* command (I or V)
* primary
* secondary
* scope
There is also a scope trigger (in the rear)

Gains: actually these are additional gains

"""
import ctypes
import functools
import os
import logging
import board

__all__ = ['MultiClampChannel', 'MultiClamp']

NO_ERROR = 6000

primary_signal_VC_index = {'I' : 0,
                           'V' : 1,
                           'Ve' : 2, # pipette potential
                           '100V' : 3, # Not sure what this is
                           'Vext' : 4,
                           'Aux1' : 5,
                           'Aux2': 6}

primary_signal_IC_index = {'V' : 7,
                           'I' : 8,
                           'Ic' : 9, # command current
                           '100V' : 10,
                           'Iext' : 11,
                           'Aux1' : 12,
                           'Aux2' : 13}

primary_signal_index = {'V' : primary_signal_VC_index,
                        'I' : primary_signal_IC_index}

secondary_signal_VC_index = {'I' : 0,
                             'V' : 1,
                             'Ve' : 2,
                             '100V' : 3, # Not sure what this is
                             'Vext' : 4,
                             'Aux1' : 5,
                             'Aux2': 6}

secondary_signal_IC_index = {'V' : 7,
                             'I' : 8,
                             'Ic' : 9, # command current
                             'Ve' : 10,
                             '100V' : 11,
                             'Iext' : 12,
                             'Aux1' : 13,
                             'Aux2' : 14}

secondary_signal_index = {'V' : secondary_signal_VC_index,
                          'I': secondary_signal_IC_index}

def needs_select(func):
    """
    Decorator for all methods of `MultiClamp` that need to select the device
    first (only calls `Multiclamp.select_amplifier` if the respective device is
    not already the selected device).
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwds):
        if not MultiClampChannel.selected_device == self:
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
    Device representing a MultiClamp amplifier with two channels or more.

    Parameters
    ----------
    channels
        List of MultiClamp channels. If none, a single 2-channel Multiclamp is assumed.
    """
    def __init__(self, *channels):
        self.channel = channels
        if len(channels) == 0: # assumes a 2-channel multiclamp
            for i in range(2):
                self.channel.append(MultiClampChannel(channel = i+1))

    def configure_board(self, theboard, primary = None, secondary = None, command = None):
        '''
        Configure an acquisition board.

        Parameters
        ----------
        primary
            A list of names of connections on the board for the primary signal, for each channel.
        secondary
            A list of names of connections on the board for the secondary signal, for each channel.
        command
            A list of names of connections on the board for the command signal, for each channel.
        '''
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

    def acquire(self, *inputs, **outputs):
        '''
        Send commands and acquire signals.

        Parameters
        ----------
        inputs
            A list of input variables to acquire. From: V1, I1, Ve1, V2, I2, etc (electrode potential)
        outputs
            A dictionary of commands. From: V1, I1, V2, I2...
        '''
        # Switch the mode
        # Sets the signals
        # Get the gains
        # Adjust the gains on the board
        pass

class MultiClampChannel(object):
    """
    Device representing a MultiClamp amplifier channel (i.e., one amplifier with
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
        self.dll = ctypes.WinDLL(os.path.join(MultiClampChannel.dll_path,
                                              'AxMultiClampMsg.dll'))
        self.last_error = ctypes.c_int(NO_ERROR)
        self.error_msg = ctypes.create_string_buffer(256)
        self.msg_handler = self.dll.MCCMSG_CreateObject(ctypes.byref(self.last_error))
        self.check_error(fail=True)
        if MultiClampChannel.all_devices is None:
            MultiClampChannel.all_devices = self.find_amplifiers()
        self.identification = kwds
        self.select_amplifier()

        # Sets the gains: depends on the headstage (feedback resistor)
        volt = 1.
        mV = 1e-3
        nA = 1e-9
        self.gain = {'V': 10*mV/mV,
                      'I': 2.5*volt/nA,
                      'Ic': 0.5*volt/nA,  # command current
                      'Ve': 1*mV/mV,
                      'Vext' : 50*mV/mV,
                      '100V': 500*mV/mV,
                      'Iext': 2.5*volt/nA,
                      'Aux1': None,
                      'Aux2': None}

        # Sets the gains on the amplifier (maybe to be done for each mode)
        self.set_primary_signal_gain(1.)
        self.set_secondary_signal_gain(1.)

    def configure_board(self, theboard, primary = None, secondary = None, command = None):
        '''
        Configure an acquisition board.

        Parameters
        ----------
        primary
            A connection name on the board for the primary signal.
        secondary
            A connection name on the board for the secondary signal.
        command
            A connection name on the board for the command signal.
        '''
        self.board = theboard
        self.primary = primary
        self.secondary = secondary
        self.command = command

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

        # Switch the mode and set the gain of the command
        outputname = outputs.keys()[0]
        if outputname == 'I':
            self.current_clamp()
        elif outputname == 'V':
            self.voltage_clamp()
        else:
            raise IndexError("Output command must be I or V.")

        # Set the gains on the amplifier
        self.set_primary_signal_gain(1.)
        self.set_secondary_signal_gain(1.)

        # Set the signals
        # TODO: possibly switch primary and secondary depending on the signal name
        self.set_primary_signal(primary_signal_index[outputname][inputs[0]])
        if len(inputs) == 2:
            self.set_secondary_signal(secondary_signal_index[outputname][inputs[1]])
            self.board.gain[self.secondary] = self.get_secondary_signal_gain()

        # Set the gains on the board
        self.board.gain[self.command] = self.gain[outputname]
        self.board.gain[self.primary] = self.gain[inputs[0]]
        self.board.gain[self.secondary] = self.gain[inputs[1]]

        return self.board.acquire()

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
        for multiclamp in MultiClampChannel.all_devices:
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
        MultiClampChannel.selected_device = self

    # **** Signal settings ****

    @needs_select
    def set_primary_signal(self, signal):
        if not self.dll.MCCMSG_SetPrimarySignal(self.msg_handler,
                                                ctypes.c_uint(signal),
                                                ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_primary_signal(self):
        res = ctypes.c_uint(0)
        if not self.dll.MCCMSG_GetPrimarySignal(self.msg_handler,
                                                ctypes.byref(res),
                                                ctypes.byref(self.last_error)):
            self.check_error()
        return res.value

    @needs_select
    def set_primary_signal_gain(self, gain):
        if not self.dll.MCCMSG_SetPrimarySignalGain(self.msg_handler,
                                                    ctypes.c_double(gain),
                                                    ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_primary_signal_gain(self):
        gain = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetPrimarySignalGain(self.msg_handler,
                                                    ctypes.byref(gain),
                                                    ctypes.byref(self.last_error)):
            self.check_error()
        return gain.value

    @needs_select
    def set_primary_signal_lpf(self, lpf):
        if not self.dll.MCCMSG_SetPrimarySignalLPF(self.msg_handler,
                                                   ctypes.c_double(lpf),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def set_primary_signal_hpf(self, hpf):
        if not self.dll.MCCMSG_SetPrimarySignalHPF(self.msg_handler,
                                                   ctypes.c_double(hpf),
                                                   ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def set_secondary_signal(self, signal):
        if not self.dll.MCCMSG_SetSecondarySignal(self.msg_handler,
                                                  ctypes.c_uint(signal),
                                                  ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_secondary_signal(self, signal):
        res = ctypes.c_uint(signal)
        if not self.dll.MCCMSG_GetSecondarySignal(self.msg_handler,
                                                  ctypes.byref(res),
                                                  ctypes.byref(self.last_error)):
            self.check_error()
        return res.value

    @needs_select
    def set_secondary_signal_lpf(self, lpf):
        if not self.dll.MCCMSG_SetSecondarySignalLPF(self.msg_handler,
                                                     ctypes.c_double(lpf),
                                                     ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def set_secondary_signal_gain(self, gain):
        if not self.dll.MCCMSG_SetSecondarySignalGain(self.msg_handler,
                                                      ctypes.c_double(gain),
                                                      ctypes.byref(self.last_error)):
            self.check_error()

    @needs_select
    def get_secondary_signal_gain(self):
        gain = ctypes.c_double(0.)
        if not self.dll.MCCMSG_GetSecondarySignalGain(self.msg_handler,
                                                    ctypes.byref(gain),
                                                    ctypes.byref(self.last_error)):
            self.check_error()
        return gain.value

    # **** Recording modes ****

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

    # **** Compensation ****

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
    def auto_pipette_offset(self):
        if not self.dll.MCCMSG_AutoPipetteOffset(self.msg_handler,
                                                 ctypes.byref(self.last_error)):
            self.check_error()

    def close(self):
        self.dll.MCCMSG_DestroyObject(self.msg_handler)
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

    amp = MultiClampChannel()
    amp.configure_board(board, primary = 'primary', secondary = 'secondary', command = 'command')

    Ic = zeros(int(1000*ms/dt))
    Ic[int(130*ms/dt):int(330*ms/dt)] += 500*pA

    Vm, Im = amp.acquire('V','I', I = Ic)
    #Vm = board.acquire('Vm', Ic = Ic)

    del board

    R = (Vm[len(Vm)/2] - Vm[0])/(500*pA)
    print R / 1e6

    subplot(211)
    plot(array(Vm)/(mV))
    subplot(212)
    plot(Im/pA)
    show()

    #amp.acquire('V')


'''
//==============================================================================================
// Function parameters
//==============================================================================================

// Parameters for MCCMSG_FindFirstMultiClamp(), MCCMSG_FindNextMultiClamp() and MCCMSG_SelectMultiClamp()
// uModel filled in / or puModel filled out as:
const int MCCMSG_HW_TYPE_MC700A                         = 0;
const int MCCMSG_HW_TYPE_MC700B                         = 1;

// Parameters for MCCMSG_SetMode() and MCCMSG_GetMode()
// uModeID filled in / or puModeID filled out as:
const UINT MCCMSG_MODE_VCLAMP                           = 0;
const UINT MCCMSG_MODE_ICLAMP                           = 1;
const UINT MCCMSG_MODE_ICLAMPZERO                       = 2;

// Parameters for MCCMSG_QuickSelectButton()
// uButtonID filled in as:
const UINT MCCMSG_QSB_1                                 = 0;
const UINT MCCMSG_QSB_2                                 = 1;
const UINT MCCMSG_QSB_3                                 = 2;

// Parameters for MCCMSG_SetPrimarySignal(), MCCMSG_SetPrimarySignal()
// uSignalID filled in / or puSignalID filled out as:
const UINT MCCMSG_PRI_SIGNAL_VC_MEMBCURRENT             = 0;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_VC_MEMBPOTENTIAL           = 1;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_VC_PIPPOTENTIAL            = 2;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_VC_100XACMEMBPOTENTIAL     = 3;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_VC_EXTCMDPOTENTIAL         = 4;  // 700B only
const UINT MCCMSG_PRI_SIGNAL_VC_AUXILIARY1              = 5;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_VC_AUXILIARY2              = 6;  // 700B only

const UINT MCCMSG_PRI_SIGNAL_IC_MEMBPOTENTIAL           = 7;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_IC_MEMBCURRENT             = 8;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_IC_CMDCURRENT              = 9;  // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_IC_100XACMEMBPOTENTIAL     = 10; // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_IC_EXTCMDCURRENT           = 11; // 700B only
const UINT MCCMSG_PRI_SIGNAL_IC_AUXILIARY1              = 12; // 700B and 700A
const UINT MCCMSG_PRI_SIGNAL_IC_AUXILIARY2              = 13; // 700B only

// Parameters for MCCMSG_SetSecondarySignal(), MCCMSG_SetSecondarySignal()
// uSignalID filled in / or puSignalID filled out as:
const UINT MCCMSG_SEC_SIGNAL_VC_MEMBCURRENT             = 0;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_VC_MEMBPOTENTIAL           = 1;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_VC_PIPPOTENTIAL            = 2;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_VC_100XACMEMBPOTENTIAL     = 3;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_VC_EXTCMDPOTENTIAL         = 4;  // 700B only
const UINT MCCMSG_SEC_SIGNAL_VC_AUXILIARY1              = 5;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_VC_AUXILIARY2              = 6;  // 700B only

const UINT MCCMSG_SEC_SIGNAL_IC_MEMBPOTENTIAL           = 7;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_IC_MEMBCURRENT             = 8;  // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_IC_CMDCURRENT              = 9;  //          700A only
const UINT MCCMSG_SEC_SIGNAL_IC_PIPPOTENTIAL            = 10; // 700B only
const UINT MCCMSG_SEC_SIGNAL_IC_100XACMEMBPOTENTIAL     = 11; // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_IC_EXTCMDCURRENT           = 12; // 700B only
const UINT MCCMSG_SEC_SIGNAL_IC_AUXILIARY1              = 13; // 700B and 700A
const UINT MCCMSG_SEC_SIGNAL_IC_AUXILIARY2              = 14; // 700B only

// Parameters for MCCMSG_GetMeterValue()
const UINT MCCMSG_METER1                                = 0;  // 700B
const UINT MCCMSG_METER2                                = 1;  // 700B
const UINT MCCMSG_METER3                                = 2;  // 700B
const UINT MCCMSG_METER4                                = 3;  // 700B
'''
