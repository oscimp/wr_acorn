import numpy as np
from matplotlib import pyplot as plt
from migen import *
from migen.genlib.cdc import MultiReg

from litex.gen import *
from litex.soc.integration.soc import *


class NonLinearityLUT(LiteXModule):
    def __init__(self, lut=None, int_size=8, frac_size=24,  n=112):
        if lut is None:
            lut = [1 << frac_size] * n
        else :
            lut = list(map(int, np.round(lut * (1 << frac_size))))

        self.step_up = Signal(frac_size + int_size, reset=lut[0])
        self.step_down = Signal(frac_size + int_size, reset=lut[-1])
        

        self.lut_shift = Signal()
        self.sign  = Signal()

        self.write_en = Signal()
        self.write_val = Signal(frac_size + int_size)

        # # #

        self.specials.mem = mem = Memory(int_size+frac_size, n, init=lut)

        self.rwport = rwport = mem.get_port(write_capable=True)
        ram_buf = Signal(frac_size + int_size)
        ram_latency = 5 # shift to valid steps

        self.count = count = Signal(max=n+1)
        ram_busy = Signal(max=ram_latency + 1)
        load_up = Signal()
        load_down = Signal()
        self.sync += [
                ram_buf.eq(rwport.dat_r),
                rwport.dat_w.eq(self.write_val),
                If(self.lut_shift,
                    ram_busy.eq(ram_latency),
                    If(self.sign,
                        count.eq(Mux(count == 0,
                            n-1,
                            count - 1,
                        )),
                        self.step_up.eq(self.step_down),
                        load_down.eq(1),
                    ).Else(
                        count.eq(Mux(count == n-1,
                            0,
                            count + 1,
                        )),
                        self.step_down.eq(self.step_up),
                        load_up.eq(1),
                    ),
                ),
                If(load_up,
                    rwport.adr.eq(count),
                ).Elif(load_down,
                    rwport.adr.eq(Mux(count == 0,
                            n-1,
                            count - 1,
                        )),
                ),
                If(ram_busy,
                   ram_busy.eq(ram_busy - 1),
                ).Else(
                    If(load_up,
                       self.step_up.eq(ram_buf),
                       load_up.eq(0),
                    ).Elif(load_down,
                       self.step_down.eq(ram_buf),
                       load_down.eq(0),
                    ),
                    If(~self.write_en,
                        If(rwport.we,
                           rwport.we.eq(0),
                        ),
                    ).Else(
                        rwport.we.eq(1),
                        rwport.adr.eq(Mux(count == 0,
                                n-1,
                                count - 1,
                            )),
                    ),
                )
            ]

        self.stat = CSRStatus(fields=[
            CSRField("addr", size=8, offset=0),
            CSRField("val", size=24, offset=8),
            ])

        self.comb += [
                self.stat.fields.addr.eq(count),
                self.stat.fields.val.eq(ram_buf),
            ]

        


def get_trace(filename):
    r = open(filename, 'r').read()
    b, r = r.split('TIC ', maxsplit=1)
    r = r.split('\n', maxsplit=1)[1]
    r = r.split(';', maxsplit=1)[0]
    r = r.strip()
    r = r.split()
    r = list(map(float, r))

    return np.array(r)

def find_steps(arr, min_stable=2000, thr=8e-12):
    a = 0
    b = 1
    while b < len(arr):
        m = arr[a]
        while b-a <= min_stable or (b < len(arr) and abs(arr[b] - m) < thr):
            b += 1
            if b-a == min_stable:
                m = np.mean(arr[a:b])
        if b - a > 10:
            yield np.mean(arr[a:b-10]), b - 10 - a
        a = b + 9
        b += 10

def steps_to_lut(steps, n=112, inv_dir=False):
    p = np.array([x[0] for x in steps])
    d = p[1:] - p[:-1]
    if inv_dir:
        d = p[:-1] - p[1:]
    lut = np.array([np.mean(d[s::n]) for s in range(n)])
    if inv_dir:
        lut = lut[::-1]
    lut *= n / np.sum(lut)
    return lut

def lut_from_trace(filename, inv=False):
    return steps_to_lut(find_steps(get_trace(filename)), inv_dir=inv)
