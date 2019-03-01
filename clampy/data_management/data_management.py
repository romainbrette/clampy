'''
Data management tools
'''
import collections
import os
import textwrap
from datetime import datetime
import inspect
import json
import time

import numpy as np

__all__ = ['date_time', 'save_info', 'current_script', 'save_current_script',
           'current_filename', 'SessionRecorder']

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

def save_current_script(filename = None, path = ''):
    '''
    Saves the current script.

    Note: copying the file directly would be simpler.
    '''
    if filename is None:
        filename = current_filename() # Doesn't work: you first need to remove the path
    filename = path+filename
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


class SessionRecorder(object):
    def __init__(self, basedir, dt):
        self.dt = float(dt)
        self.basedir = basedir
        if not os.path.exists(self.basedir):
            os.makedirs(self.basedir)
        self.start_time_real = None
        self.start_time_counter = None
        self.recordings = collections.defaultdict(list)

    def start_recording(self):
        self.start_time_real = datetime.now()
        self.start_time_counter = time.time()

    def stop_recording(self):
        formatted_time = self.start_time_real.strftime('%H:%M:%S')
        basename = 'recording_' + formatted_time
        dict_of_arrays = {name: np.array(list(zip(*values)))
                          for name, values in self.recordings.items()}
        np.savez_compressed(os.path.join(self.basedir, basename + '.npz'),
                            **dict_of_arrays)
        with open(os.path.join(self.basedir, basename + '_info.txt'),
                  'wt') as f:
            header = textwrap.dedent('''\
            Voltage clamp data
            ------------------

            Start of recording: {start}

            Each array in "{fname}" stores one data point in each row.
            The first column stores an increasing index that enumerates all stimulations.
            In general this counter  does not start at 0, because it includes repetitions
            before the start of the recording. The second column stores the time in seconds 
            since the start of the recording, all further columns are recorded data.

            Recorded data:
            ~~~~~~~~~~~~~~
            '''.format(fname=basename + '.npz',
                       start=self.start_time_real.strftime('%c')))
            f.write(header + '\n')
            for name, values in sorted(dict_of_arrays.items()):
                f.write('{}: {} × {}\n'.format(name,
                                               values.shape[0],
                                               values.shape[1]))

    def record(self, name, sample, sample_start, *value_args):
        if name not in self.recordings:
            self.recordings[name] = [[] for _ in range(2 + len(value_args))]
        time_points = (sample_start - self.start_time_counter) + np.arange(len(value_args[0])) * self.dt
        self.recordings[name][0].extend([sample] * len(time_points))
        self.recordings[name][1].extend(time_points)
        for value_idx, values in enumerate(value_args):
            self.recordings[name][2 + value_idx].extend(values)