'''
Axon Digidata 1322A
'''
from board import *

__all__ = ['Board']

class Digidata1322A(Board):
    '''
    A generic acquisition board
    '''
    def __init__(self):
        Board.__init__(self)

    def set_analog_input(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_analog_input(name, channel, gain)

    def set_analog_output(self, name, channel=None, gain=None):
        '''
        Sets the mapping between channel names and channel numbers,
        and the conversion factor.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_analog_output(name, channel, gain)

    def set_digital_output(self, name, channel=None):
        '''
        Sets the mapping between channel names and channel numbers.

        Parameters
        ----------
        channel : channel number (starting from 0)
        gain : conversion factor (input unit/volt)
        '''
        Board.set_digital_output(name, channel)
