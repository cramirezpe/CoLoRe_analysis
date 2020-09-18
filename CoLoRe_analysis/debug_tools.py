import functools
import pdb
import sys
import time
import traceback
from contextlib import contextmanager


@contextmanager
def debug_on_context(*exceptions): #pragma: no cover
    if not exceptions:
        exceptions = (AssertionError, )
    def context():
        try:
            yield
        except exceptions:
            info = sys.exc_info()
            traceback.print_exception(*info)
            pdb.post_mortem(info[2])
    return context()

def debug_on(*exceptions): #pragma: no cover
    if not exceptions:
        exceptions = (AssertionError, )
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                info = sys.exc_info()
                traceback.print_exception(*info) 
                pdb.post_mortem(info[2])
        return wrapper
    return decorator

class Stopwatch(): #pragma: no cover
    def __init__(self):
        self.start_time = time.process_time()
        self.lap_times = []
    
    def lap(self, message=None):
        try:
            lap_time = time.process_time() - self.lap_times[-1]
        except IndexError:
            lap_time = time.process_time() - self.start_time
        self.lap_times.append(lap_time)
        if message is None:
            print('Stopwatch Lap\t', lap_time)
        else:
            print('Stopwatch Lap. ', message, ':\t', lap_time)
        return lap_time

    def full(self, message=None):
        full_time = time.process_time() - self.start_time
        if message is None:
            print('Stopwatch Global\t', full_time)
        else:
            print('Stopwatch Global. ', message, ':\t', full_time)
        return full_time
