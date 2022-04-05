'''
Control Axoclamp GUI by clicking

pyautogui.mouseInfo() to get coordinates and pixel colors
'''
import pygetwindow
import pyautogui

x, y, w, h = pygetwindow.getWindowGeometry('Axoclamp')

# On-off settings can be read from pixels
