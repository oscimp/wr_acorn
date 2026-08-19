from migen import *
from migen.genlib.cdc import MultiReg

from litex.gen import *
from litex.soc.integration.soc import *

from litescope import LiteScopeAnalyzer

# Phase Shift Generator -----------------------------------------------------------------------------

class SigmaDeltaPSGen(LiteXModule):
    def __init__(self, int_size=8, frac_size=24, wait_time=12):

        # Control Interface.
        self.rate = Signal((frac_size, True))
        self.dither_en = Signal()
        self.step_up = Signal(frac_size + int_size, reset=1<<frac_size)
        self.step_down = Signal(frac_size + int_size, reset=1<<frac_size)

        # LUT interface
        self.lut_shift = Signal() # asserted when the phase shift is permanent, and not for sigmadelta

        # Phase Shift Interface.
        self.shift = Signal()
        self.sign  = Signal()

        # # #


        wait12 = Signal(4)
        acc = Signal((int_size + frac_size, True))
        phy = Signal.like(acc) # actual aplied phase
        sd_acc = Signal.like(acc)

        sd_is_up = Signal()
        sd_was_up = Signal()

        carry_up = Signal()
        carry_down = Signal()
        
        sd_up = Signal()
        sd_down = Signal()
        main_up = Signal()
        main_down = Signal()

        up = Signal()
        down = Signal()
        

        delta = Signal((4, True))
        #signed = lambda s: Cat(s, Replicate(0, 4-len(s)))
        def signed(s, size=4):
            ss = Signal((size, True))
            self.comb += ss.eq(s)
            return ss

        self.fsm = fsm = FSM()
        fsm.act('TICK',
                delta.eq((signed(main_up) - signed(main_down)) + \
                         (signed(carry_up) - signed(carry_down)) + \
                         Mux(self.dither_en,
                            signed(sd_up) - signed(sd_down),
                            0
                        )
                ),

                up.eq(delta >= 1),
                down.eq((delta == -1) | (delta == -2)),
                NextValue(carry_up, delta == 2),
                NextValue(carry_down, delta == -2),

                If(up,
                    NextValue(self.shift, 1),
                    NextValue(self.sign, 0),
                ),
                If(down,
                    NextValue(self.shift, 1),
                    NextValue(self.sign, 1),
                ),
                NextState('ACCUMULATE'),
            )
        fsm.act('ACCUMULATE',
                NextValue(self.shift, 0),
                NextValue(acc, acc + self.rate),
                NextValue(sd_acc, sd_acc + (acc - phy)),
                NextState('WRAPAROUND'),
            )
        fsm.act('WRAPAROUND',
                If(self.rate >= 0,
                    If(sd_acc >= self.step_up,
                        NextValue(sd_acc, sd_acc - self.step_up),
                        sd_is_up.eq(1),
                    ).Else(
                        sd_is_up.eq(0),
                    ),
                ).Else(
                    If(sd_acc <= -self.step_down,
                        NextValue(sd_acc, sd_acc + self.step_down),
                        sd_is_up.eq(0),
                    ).Else(
                        sd_is_up.eq(1),
                    ),
                ),
                NextValue(sd_was_up, sd_is_up),
                NextValue(sd_up, sd_is_up & ~sd_was_up),
                NextValue(sd_down, ~sd_is_up & sd_was_up),
                
                If(acc >= self.step_up,
                    NextValue(acc, acc - self.step_up),
                    NextValue(phy, acc - self.step_up),
                    NextValue(main_up, 1),
                    NextValue(self.sign, 0),
                    NextValue(self.lut_shift, 1),
                ).Else(
                    NextValue(main_up, 0),
                ),
                If(acc <= -self.step_down,
                    NextValue(acc, acc + self.step_down),
                    NextValue(phy, acc + self.step_down),
                    NextValue(main_down,1),
                    NextValue(self.sign, 1),
                    NextValue(self.lut_shift, 1),
                ).Else(
                    NextValue(main_down, 0),
                ),
                NextValue(wait12, wait_time-2-2),
                NextState('WAIT'),
            )
        fsm.act('WAIT',
                NextValue(self.lut_shift, 0),
                NextValue(wait12, wait12 - 1),
                If(wait12 == 0,
                    NextState('TICK'),
                ),
            )


        self.dbg = Signal()
        #self.dbg_mux_sel = CSRStorage(size=8)
        #self.comb += self.dbg.eq(Array([
        #        self.shift,
        #        self.sign,
        #        sd_up,
        #        sd_down,
        #        main_up,
        #        main_down,
        #        carry_up,
        #        carry_down,
        #        delta[0],
        #        delta[1],
        #        delta[2],
        #        delta[3],
        #        ])[self.dbg_mux_sel.storage]
        #    )


        ### ILA
        if False:
            self.analyzer = LiteScopeAnalyzer([
                    self.shift,
                    self.sign,
                    sd_up,
                    sd_down,
                    main_up,
                    main_down,
                    carry_up,
                    carry_down,
                    delta,
                    up,
                    down,
                ],
                depth        = 8000,
                register     = True,
                csr_csv      = "sigmadelta_analyzer.csv"
            )

def sim(sd=True):
    from migen.sim import run_simulation

    dut = SigmaDeltaPSGen(8, 24, 4)

    def case1():
        nl = [
                int(1.5 * (1<<24)),
                int(0.75* (1<<24)),
                int(1.0* (1<<24)),
                int(1.2* (1<<24)),
            ]
        phi = 0
        i = 0
        it = 0
        a = []
        yield dut.rate.eq(90140)
        yield dut.dither_en.eq(sd)
        yield dut.step_up.eq(nl[i%len(nl)])
        yield dut.step_down.eq(nl[(i-1)%len(nl)])
        for _ in range(10000):
            yield
            d = (-1)**(yield dut.sign)
            if (yield dut.shift):
                phi += nl[(it-(yield dut.sign))%len(nl)] * d
                it += d
            if (yield dut.lut_shift):
                i += d
                yield dut.step_up.eq(nl[i%len(nl)])
                yield dut.step_down.eq(nl[(i-1)%len(nl)])
            a.append(phi)
        open(f'phase{'_sd' if sd else ''}.sim','w').write(str(a))

    
    run_simulation(dut, case1(), vcd_name=f'sim{'_sd'if sd else''}.vcd')
