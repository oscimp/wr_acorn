#!/usr/bin/env python3

#

from migen import *
from migen.genlib.resetsync import *

from litex.gen import *


from gateware.sigmadelta import SigmaDeltaPSGen
from gateware.nonlin_lut import *
from gateware.dmtd import *


# BaseSoC ------------------------------------------------------------------------------------------

class SelfCalibCtrl(LiteXModule):
    def __init__(self,
                 int_size=8,
                 frac_size=24,
                 n=112,
                 tag_size=14,
                 nb_tags_avg=2**14):
        # Phase shift ctrl output
        self.shift = Signal()
        self.sign = Signal()

        # LUT output
        self.we = Signal()
        self.val = Signal(int_size + frac_size)

        # DMTD tag input
        self.tag = Signal(tag_size)
        self.tag_rdy = Signal()

        # Misc.
        self.done = Signal() # out
        self.ready = Signal() # out
        self.start = Signal() # in


        ###############################

        pos_cnt = Signal(max=n + 1)
        tag_cnt = Signal(max=nb_tags_avg+1)
        
        acc_tags = Signal(int_size + frac_size)

        prev_tag = Signal.like(acc_tags)
        
        wait_cnt = Signal(max=12 +1)

        has_prev_tag = Signal()

        def sign(s):
            return Cat(s, Replicate(s[-1], int_size + frac_size - len(s)))

        self.fsm = fsm = FSM()
        fsm.act('IDLE',
                self.ready.eq(1),
                NextValue(pos_cnt, 0),
                NextValue(tag_cnt, 0),
                NextValue(acc_tags, 0),
                NextValue(prev_tag, 0),
                NextValue(has_prev_tag, 0),
                If(self.start,
                    NextValue(self.done, 0),
                    NextState('ACC_TAGS'),
                )
            )
        fsm.act('ACC_TAGS',
                If(tag_cnt == nb_tags_avg,
                    If(has_prev_tag,
                       NextState('WRITE_LUT'),
                    ).Else(
                        NextValue(prev_tag, acc_tags),
                        NextValue(has_prev_tag, 1),
                        NextState('SHIFT'),
                    )
                ).Elif(self.tag_rdy,
                   NextValue(acc_tags, acc_tags + self.tag),
                   NextValue(tag_cnt, tag_cnt + 1),
                ),
            )
        fsm.act('WRITE_LUT',
                NextValue(pos_cnt, pos_cnt + 1),
                NextValue(self.val, acc_tags - prev_tag),
                NextValue(self.we, 1),
                NextValue(prev_tag, acc_tags),
                NextState('SHIFT'),
            )
        fsm.act('SHIFT',
                NextValue(self.we, 0),
                NextValue(self.shift, 1),
                NextValue(self.sign, 0),
                NextValue(wait_cnt, 0),
                NextState('WAIT_SHIFT'),
            )
        fsm.act('WAIT_SHIFT',
                NextValue(self.shift, 0),
                If(wait_cnt == 12,
                    If(pos_cnt == n,
                        NextValue(self.done, 1),
                        NextState('IDLE'),
                    ).Else(
                        NextValue(acc_tags, 0),
                        NextValue(tag_cnt, 0),
                        NextState('ACC_TAGS'),
                    )
                ).Else(
                    NextValue(wait_cnt, wait_cnt + 1),
                )
            )
        # TODO simulation
