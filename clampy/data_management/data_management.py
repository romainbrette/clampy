'''
Data management tools
'''
from future.utils import iteritems
import collections
import os
import textwrap
from datetime import datetime
import inspect
import warnings
import io
import shutil

try:
    import json
except ImportError:
    warnings.warn('JSON support is not available')
try:
    import yaml
except ImportError:
    warnings.warn('YAML support is not available')
import time
import gzip
import numpy as np
import sys
import re
import uuid

__all__ = ['date_time', 'save_info', 'current_script', 'save_current_script',
           'current_filename', 'SessionRecorder', 'load_info', 'load_data',
           'print_and_log', 'load_dataset']

def print_and_log(filename, s):
    '''
    Print to file filename and to stdout.
    '''
    print(s)
    with open(filename, 'a+') as f:
        f.write(s+'\n')

def date_time():
    '''
    Returns a string consisting of date and time
    '''
    t = datetime.now()
    return '{}.{}.{} {}.{}.{}'.format(t.day, t.month, t.year, t.hour, t.minute, t.second)

def load_dataset(filename, copy_first=False, first_only=False):
    '''
    Loads a set of data files, of the form filename???.txt or .txt.gz or .npz
    If t is a variable, it is assumed to be identical in all trials (possibly with different durations).
    Assuming numbering from 0 to n, or no number at all.
    If first_only is True, loads only the first trial.

    Returns a dictionary of signals, each signal being a matrix (row = trial, column = time).
    Trials are trimmed to the minimum duration over trials.
    '''
    folder, name = os.path.split(filename)
    pattern = re.compile(name+r'(\d*)\.(txt|txt\.gz|npz)$')

    # Sort trials
    files = []
    for f in os.listdir(folder):
        result = pattern.match(os.path.split(f)[1])
        if result is not None:
            if result.group(1) == '':
                n = 0
            else:
                n = int(result.group(1))
            files.append((n,os.path.join(folder,f)))
    files.sort()
    if first_only:
        files = files[:1]

    if len(files)==0:
        return None

    # Load files
    all_signals = {}
    min_size = 1e20
    i = 0
    for _, file in files:
        signals = load_data(file, copy_first=copy_first)
        if len(signals[list(signals.keys())[0]])<min_size:
            min_size = len(signals[list(signals.keys())[0]])
        if i == 0:
            all_signals = {x : [y] for x,y in signals.items() if (x is not 't') and (len(y.shape)>0)} # remove scalars
        else:
            all_signals = {x : all_signals[x]+[y] for x,y in signals.items() if (x is not 't') and (len(y.shape)>0)}
        i += 1

    # Cut at minimum size (trials could have different sizes)
    if 't' in signals:
        all_signals['t'] = signals['t'][:min_size]
    for key in all_signals:
        if (key != 't'):
            all_signals[key] = [signal[:min_size] for signal in all_signals[key]]

    # Turn to arrays
    all_signals = {x: np.array(all_signals[x]) for x, y in all_signals.items()}

    return all_signals


def load_dataset_old(filename, copy_first=False, first_only=False):
    '''
    Loads a set of data files, of the form filename???.txt or .txt.gz or .npz
    Assuming numbering from 0 to n, or no number at all.

    If first_only is True, loads only the first trial.

    OLD VERSION
    '''
    dir, name = os.path.split(filename)
    if dir == '':
        dir = '.'
    pattern = re.compile(os.path.split(filename)[1]+r'(\d*)\.(txt|txt\.gz|npz)$')

    # Determine extension and number of trials
    ntrials = -1
    ext = ''
    numbering = True
    for f in os.scandir(dir):
        result = pattern.match(os.path.split(f.path)[1])
        if result is not None:
            if result.group(1) == '':
                n = 0
                numbering = False
            else:
                n = int(result.group(1))
            if n>ntrials:
                ntrials = n
                ext = '.'+result.group(2)
    ntrials += 1

    if ntrials >0:
        # Load files
        all_signals = {}
        min_size = 1e20
        if first_only:
            ntrials = 1
        for i in range(ntrials):
            if numbering:
                signals = load_data(os.path.join(dir,name+str(i)+ext), copy_first=copy_first)
            else:
                signals = load_data(os.path.join(dir,name+ext), copy_first=copy_first)
            if (len(signals['t'])<min_size):
                min_size = len(signals['t'])
            if i == 0:
                all_signals = {x : [y] for x,y in signals.items() if (x is not 't') and (len(y.shape)>0)} # remove scalars
                t = signals['t']
            else:
                all_signals = {x : all_signals[x]+[y] for x,y in signals.items()  if (x is not 't') and (len(y.shape)>0)}

        # Cut at minimum size (trials could have different sizes)
        all_signals['t'] = t[:min_size]
        for key in all_signals:
            if (key != 't'):
                all_signals[key] = [signal[:min_size] for signal in all_signals[key]]

        # Turn to arrays
        all_signals = {x: np.array(all_signals[x]) for x, y in all_signals.items()}

        return all_signals
    else:
        return None

def load_data(filename, copy_first=False):
    '''
    Loads a data file, .npz, or .txt or .txt.gz, with the following conventions:
    - header gives variable names (separated by spaces)
    - one column = one variable
    Returns a dictionary of signals
    '''
    _, ext = os.path.splitext(filename)

    if copy_first:
        newfilename = str(uuid.uuid4())+ext
        #shutil.copy(filename,newfilename)
        os.system('cp "{}" "{}"'.format(filename,newfilename))
        filename = newfilename

    # Get variable names
    if ext == '.gz': # compressed
        if sys.version_info.major == 2: # Python 2
            f = gzip.open(filename, mode='r')
        else: # Python 3
            f = gzip.open(filename, mode='rt')
    elif ext == '.npz':
        return np.load(filename)
    else: # assuming text
        f = open(filename, 'r')
    variables = f.readline().split()
    f.close()

    # Load signals
    if len(variables) == 1:
        signals = { variables[0]: np.loadtxt(filename, skiprows=1, unpack=True)}
    else:
        signals = {}
        for name, value in zip(variables, np.loadtxt(filename, skiprows=1, unpack=True)):
            signals[name] = value

    # Clean up
    if copy_first:
        os.remove(newfilename)

    return signals

def save_info(filename, **parameters):
    '''
    Saves a dictionary of script information.
    Units of numbers, lists and arrays are discarded.

    Parameters
    ----------
    filename : file name
    parameters : parameters and their values
    '''
    # Remove Brian units and turn arrays into lists (only works for 1D arrays)
    d=dict()
    for key, value in iteritems(parameters):
        if (isinstance(value, list)) and list != []: # list
            try:
                value[0].dimensions
                d[key] = [float(x) for x in value]
            except AttributeError:
                if isinstance(value[0],float): # could be a numpy float
                    d[key] = [float(x) for x in value]
                else:
                    d[key] = list(value)
        elif (isinstance(value, np.ndarray) and len(value.shape)==1): # 1D array
            d[key] = [float(x) for x in value]
        else:
            try:
                value.dimensions
                d[key] = float(value)
            except AttributeError:
                d[key] = value

    # Deduce format from the extension
    _,ext = os.path.splitext(filename)

    with open(filename, 'w') as fp:
        if ext == '.json':
            json.dump(d, fp)
        elif ext == '.yaml':
            yaml.dump(d, fp)
        else:
            raise IOError('Format .{} is unknown'.format(ext))

def load_info(filename):
    '''
    Loads a dictionary of script information.
    '''
    # Deduce format from the extension
    _,ext = os.path.splitext(filename)

    with open(filename, 'r') as fp:
        if (ext == '.json') or (ext == '.info'):
            d = json.load(fp)
        elif ext == '.yaml':
            d = yaml.safe_load(fp)
        else:
            raise IOError('Format .{} is unknown'.format(ext))
    return d

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
                f.write('{}: {} x {}\n'.format(name,
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
