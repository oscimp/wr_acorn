#!/usr/bin/env python3

import serial
import argparse
import time
import numpy as np
from matplotlib import pyplot as plt

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

def read_lut_map_csr_csv(filename):
    f = 'csr_base,clocking_sd_lut_mem'
    with open(filename) as file:
        r = file.read()
        for l in r.split('\n'):
            if l.startswith(f):
                return int(l.split(',')[2])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--device', metavar='TTY', default=device)
    parser.add_argument('--csr', metavar='CSR.csv')
    parser.add_argument('--addr', metavar='LUT_ADDR', default=0xf00000000)
    parser.add_argument('-l', '--load', metavar='CALIB_FILE')
    parser.add_argument('-d', '--dump', metavar='CALIB_FILE')
    
    args = parser.parse_args()
    
    if not args.addr:
        addr = read_lut_map_csr_csv(args.csr)
    else:
        addr = args.addr

    s = serial.Serial(args.device, baudrate=baudrate)
    if args.dump:
        lut = read_lut(s, addr)
        open(args.dump, 'w').write('\n'.join(lut))

    if args.load:
        write_lut(s, map(float, open(args.load).read().split()), addr)

if __name__ == '__main__':
    main()
