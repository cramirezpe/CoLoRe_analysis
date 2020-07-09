import pdb
import functools
import traceback
import sys
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