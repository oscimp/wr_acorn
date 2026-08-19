import numpy as np
from matplotlib import pyplot as plt
import time
import os

def get_trace(filename):
    r = open(filename, 'r').read()
    b, r = r.split('TIC ', maxsplit=1)
    r = r.split('\n', maxsplit=1)[1]
    r = r.split(';', maxsplit=1)[0]
    r = r.strip()
    r = r.split()
    r = list(map(float, r))

    b = b.split('Time/Date" ', maxsplit=1)[1].split('\n', maxsplit=1)[0]
    x = time.mktime(time.strptime(b,'%m/%d/%Y %I:%M:%S %p'))
    
    return x, np.array(r)

