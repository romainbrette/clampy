'''
Data management tools
'''
from datetime import datetime
import csv
import inspect
import json

__all__ = ['date_time', 'save_info', 'current_script', 'save_current_script',
           'current_filename']

def date_time():
    '''
    Returns a string consisting of date and time
    '''
    t = datetime.now()
    return '{}.{}.{} {}.{}.{}'.format(t.year, t.month, t.day, t.hour, t.minute, t.second)

def save_info(d, filename):
    '''
    Saves a dictionary of script information.
    Note that
    '''
    f = open(filename,'w')
    f.write(json.dumps(d))
    f.close()

def current_script():
    '''
    Returns the current script.
    '''
    return inspect.getsource(inspect.getmodule(inspect.currentframe(1)))

def save_current_script(filename):
    '''
    Saves the current script.
    '''
    # Get the text of the calling script
    f = open(filename, 'w')
    script = inspect.getsource(inspect.getmodule(inspect.currentframe(1)))
    # Add a line that can be used to run the script in analysis mode
    # script = 'do_experiment = False\n' + script
    f.write(script)
    f.close()

def current_filename():
    return inspect.getfile(inspect.getmodule(inspect.currentframe(1)))

def notes_file(filename):
    # Creates an empty notes file
    pass