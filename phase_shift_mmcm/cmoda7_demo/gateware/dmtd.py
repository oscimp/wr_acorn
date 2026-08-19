from migen import *
from migen.genlib.cdc import MultiReg

from litex.gen import *
from litex.soc.integration.soc import *

class DMTD(LiteXModule):
    def __init__(self, size=16, threshold=1500):
        self.clk_in = Signal()

        self.tag  = Signal(size)
        self.rdy  = Signal()

        # # #

        counter = Signal(size)
        self.sync += counter.eq(counter + 1)

        sampled_metastable = Signal()
        sampled = Signal()
        self.sync += sampled_metastable.eq(self.clk_in)
        self.sync += sampled.eq(sampled_metastable)

        
        thr_cnt = Signal(max=threshold)
        glitches_start = Signal(size)
        glitches_count = Signal(size)
        self.fsm = fsm = FSM()
        fsm.act('WAIT_STABLE_ZERO',
                NextValue(self.rdy, 0),
                If(sampled == 1,
                   NextValue(thr_cnt, 0),
                ).Elif(thr_cnt == threshold,
                       NextState('WAIT_GLITCHES'),
                ).Else(
                   NextValue(thr_cnt, thr_cnt + 1),
                ),
            )
        fsm.act('WAIT_GLITCHES',
                If(sampled == 1,
                    NextValue(glitches_start, counter),
                    NextValue(glitches_count, 0),
                    NextValue(thr_cnt, 0),
                    NextState('COUNT_GLITCHES'),
                ),
            )
        fsm.act('COUNT_GLITCHES',
                If(sampled == 0,
                   NextValue(thr_cnt, 0),
                   NextValue(glitches_count, glitches_count + 1)
                ).Elif(thr_cnt == threshold,
                       NextValue(self.tag, glitches_start + glitches_count),
                       NextValue(self.rdy, 1),
                       NextState('WAIT_STABLE_ZERO'),
                ).Else(
                   NextValue(thr_cnt, thr_cnt + 1),
                ),
            )
        
