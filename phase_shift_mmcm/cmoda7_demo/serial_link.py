#!/usr/bin/env python3

import serial
import time
import os
import re

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from scipy.signal import welch, detrend

device = '/dev/ttyUSB1'
baudrate = 115200

def ask(s, cmd):
    s.write(b'\n')
    s.flush()
    time.sleep(0.1)
    s.reset_input_buffer()
    for c in f'{cmd}\n':
        s.write(c.encode())
        print(c, end='')
        time.sleep(0.05)
    return s.read_until(b'> ').decode()

def read_lut(s, lut_addr=0xf0000000):
    r = ask(s, f'mem_read {lut_addr} {112*4}')
    print(r)
    m = np.array(sum(list(map(lambda l: list(map(lambda x: int(x, 16), l.split()[1:17])), r.split('\n')[2:-1])), start=[]))
    l = m[0::4] + 0x100 * m[1::4] + 0x10000*m[2::4] + 0x1000000*m[3::4]
    l = l / 2**24
    return l

def write_lut(s, l, lut_addr=0xf0000000):
    for i, c in enumerate(l):
        ask(s, f'mem_write {lut_addr + 4*i} {int(round(c*2**24))}')
