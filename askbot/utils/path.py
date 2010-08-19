import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else: 
            raise e
