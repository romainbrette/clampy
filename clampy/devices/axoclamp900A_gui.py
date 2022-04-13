'''
Control of the Axoclamp 900A commander panel.

TODO: maybe give the focus back to the currently active window
'''
import pyautogui as auto
import time

__all__ = ['AxoclampController']

capa_check = (36, 269)
capa_value = (215, 268)
offset_lock = (294, 228)
offset_zero = (316, 233)
detect_oscillation = (33, 376)
disable_neutralization = (50, 392)
reduce_neutralization = (50, 407)
holding_check = (33, 222)
holding_value = (106, 224)
VC_gain = (80, 308)
VC_lag = (95, 330)
VC_detect_oscillation = (34, 362)
VC_minimum_gain = (50, 381)
VC_reduce_gain = (50, 399)

tab = {'I1' : (54, 193),
       'I2' :(202, 193),
       'dSEVC' : (126, 193),
       'TEVC' : (276, 193)}

mode_button = [{'I0' : (26, 139),
                 'IC' : (69, 141),
                 'DCC' : (101, 140),
                 'dSEVC' : (171, 139)},
                {'I0' : (228, 140),
                 'IC' : (268, 139),
                 'HVIC' : (307, 139),
                 'TEVC' : (319, 140)}]

class AxoclampController(object):
    '''
    Controls the Axoclamp 900A software GUI.
    '''
    def __init__(self):
        self.window = auto.getWindowsWithTitle('Axoclamp 900A')[0]
        self.previous_window = None

    def get_focus(self):
        if not self.window.isActive:
            # Save current window
            self.previous_window = auto.getActiveWindow()
            # Bring the window in focus
            self.window.minimize()
            self.window.restore()

    def return_focus(self):
        if self.previous_window is not None:
            self.previous_window.minimize()
            self.previous_window.restore()

    def shift(self, xy):
        return (xy[0] + self.window.left, xy[1] + self.window.top)

    def quick_capacitance_neutralization(self, channel, step = 10.):
        '''
        Tunes capacitance neutralization automatically.
        This works by triggering and blocking an oscillation, so it should be done only in the bath.
        '''
        # Step size in pF
        self.set_mode(channel, 'IC')
        self.select_tab('I'+str(channel))
        self.set_capneut(0)
        self.detect_oscillation('disable')

        x = 0.8  # returns x*optimal C
        C = 0.

        while step > C * (1 - x) * .25:
            C += step
            self.set_capneut(C)
            time.sleep(.4)
            if not self.is_capaneut_on():  # assuming it will be stopped if there is an oscillation
                C -= step
            step = step * .5

        self.set_capneut(C*x)
        return C*x

    def select_tab(self, name):
        x, y = auto.position()
        auto.click(*self.shift(tab[name]))
        auto.moveTo((x,y))

    def set_mode(self, channel, mode):
        x, y = auto.position()
        auto.click(*self.shift(mode_button[channel-1][mode]))
        auto.moveTo((x,y))

    def get_mode(self, channel):
        for mode, xy in mode_button[channel - 1].items():
            if sum(auto.pixel(*self.shift(xy)))==255*3:
                return mode

    def is_holding_on(self):
        return sum(auto.pixel(*self.shift(holding_check)))==0

    def is_detect_oscillation_on(self):
        return sum(auto.pixel(*self.shift(detect_oscillation)))==0

    def is_VC_detect_oscillation_on(self):
        return sum(auto.pixel(*self.shift(VC_detect_oscillation)))==0

    def is_capaneut_on(self):
        return sum(auto.pixel(*self.shift(capa_check)))==0

    def is_offset_locked(self):
        return sum(auto.pixel(*self.shift(offset_lock)))>0

    def set_capneut(self, C):
        x, y = auto.position()
        auto.doubleClick(*self.shift(capa_value))
        auto.typewrite(str(C)+'\n')
        if not self.is_capaneut_on():
            auto.click(*self.shift(capa_check))
        auto.moveTo((x,y))

    def set_holding(self, V):
        x, y = auto.position()
        auto.doubleClick(*self.shift(holding_value))
        if V is not None:
            auto.typewrite(str(V)+'\n')
        if ((V is not None) and (not self.is_holding_on())) or (V is None and self.is_holding_on()):
            auto.click(*self.shift(holding_check))
        auto.moveTo((x,y))

    def offset_zero(self):
        x, y = auto.position()
        if self.is_offset_locked():
            auto.click(*self.shift(offset_lock))
        auto.click(*self.shift(offset_zero))
        if not self.is_offset_locked():
            auto.click(*self.shift(offset_lock))
        auto.moveTo(x,y)

    def set_VC_gain(self, gain):
        x, y = auto.position()
        auto.doubleClick(*self.shift(VC_gain))
        auto.typewrite(str(gain)+'\n')
        auto.moveTo(x,y)

    def set_VC_lag(self, lag):
        x, y = auto.position()
        auto.doubleClick(*self.shift(VC_lag))
        auto.typewrite(str(lag)+'\n')
        auto.moveTo(x,y)

    def detect_oscillation(self, mode):
        # mode in 'minimum', 'reduce', None
        x, y = auto.position()
        if ((mode == None) and self.is_detect_oscillation_on()) or (not self.is_detect_oscillation_on()):
            auto.click(*self.shift(detect_oscillation))
        if mode == 'disable':
            auto.click(*self.shift(disable_neutralization))
        elif mode == 'reduce':
            auto.click(*self.shift(reduce_neutralization))
        auto.moveTo(x,y)

    def VC_detect_oscillation(self, mode):
        # mode in 'minimum', 'reduce', None
        x, y = auto.position()
        if ((mode == None) and self.is_VC_detect_oscillation_on()) or (not self.is_VC_detect_oscillation_on()):
            auto.click(*self.shift(VC_detect_oscillation))
        if mode == 'minimum':
            auto.click(*self.shift(VC_minimum_gain))
        elif mode == 'reduce':
            auto.click(*self.shift(VC_reduce_gain))
        auto.moveTo(x,y)

if __name__ == '__main__':
    controller = AxoclampController()

    controller.set_mode(1, 'IC')
    controller.set_mode(2, 'TEVC')
    controller.select_tab('TEVC')
    controller.set_capneut(15)
    #controller.offset_zero()
    #print(controller.get_mode(1), controller.get_mode(2))
    controller.set_holding(-10)
    controller.set_VC_gain(100)
    controller.set_VC_lag(0.01)
    controller.VC_detect_oscillation('reduce')

    controller.set_mode(2, 'IC')
    controller.set_mode(1, 'IC')
    controller.select_tab('I1')
    controller.detect_oscillation('reduce')