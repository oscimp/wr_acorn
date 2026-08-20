from amaranth import Cat, ClockDomain, ClockSignal, DomainRenamer, Instance, Module, ResetSignal, Signal
from amaranth.lib.wiring import Component, In, Out

from ddmtd.deglitcher import Deglitcher
from ddmtd.fast_counter import FastCounter

class WRDDMTD(Component):
    def __init__(self, word_size=32):
        super().__init__({
            'clk_a': In(1),
            'clk_b': In(1),
            'phase': Out(word_size),
            'new_phase': Out(1),
            })
        self.word_size = word_size

    def elaborate(self, platform):
        m = Module()

        platform.add_source('dmtd_with_deglitcher.vhd')

        m.submodules.dmtd = Instance('dmtd_with_deglitcher',
                                     )

        return m
