#!/usr/bin/env python3

import serial
import time
import os
import re

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from scipy.signal import welch, detrend, correlate

import vxi11
import math
import numpy as np
import matplotlib.pyplot as plt
import time

from vxi11.vxi11 import time

baudrate = 115200
serial_dev = '/dev/ttyUSB5'

def ask(s, cmd, end=b'wrc# '):
    s.write(b'\n')
    s.flush()
    time.sleep(0.1)
    s.reset_input_buffer()
    for c in f'{cmd}\n':
        s.write(c.encode())
        print(c, end='')
        time.sleep(0.05)
    return s.read_until(end).decode()

def locksweep_done(s): # AUX locksweep
    stat = ask(s, 'pll stat')
    return "softpll: AUX0: ph:0 seq:4 en:1 lock:1" in stat

def test_fb_sync_mosquitto():
    s = serial.Serial(serial_dev, baudrate=baudrate, timeout=5)
    while True:
        ask('pll init 3 0 0')
        t1 = time.time()
        sleep(5)
        while not locksweep_done(s):
            time.sleep(1)
        lock_time = time.time() - t1
        print(lock_time)
        os.system('mosquitto_pub -h 192.168.1.170 -t locksweeping -m locksweep_done') # announce pll lock for phase statio to start acquisition
        os.system('mosquitto_sub -h 192.168.1.170 -t locksweep_now -C 1') # wait for acquisition done signal before relocking again
