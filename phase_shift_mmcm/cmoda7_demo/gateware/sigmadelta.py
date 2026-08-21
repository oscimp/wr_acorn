from migen import *
from migen.genlib.cdc import MultiReg

from litex.gen import *
from litex.soc.integration.soc import *

from litescope import LiteScopeAnalyzer

# Phase Shift Generator -----------------------------------------------------------------------------

class SigmaDeltaPSGen(LiteXModule):
    def __init__(self, int_size=8, frac_size=24, wait_time=12):

        # Control Interface.
        self.rate = Signal((int_size + frac_size, True))
        self.sigmadelta_en = Signal()
        self.step_up = Signal(frac_size + int_size, reset=1<<frac_size)
        self.step_down = Signal(frac_size + int_size, reset=1<<frac_size)

        # Phase Shift Interface.
        self.shift = Signal()
        self.sign  = Signal()

        # # #

        wait12 = Signal(max=wait_time)
        err = Signal((int_size + frac_size, True))
        sd_acc = Signal.like(err)

        up = Signal()
        down = Signal()
        
        self.fsm = fsm = FSM()
        fsm.act('T0',
                If(self.rate >= 0,
                    NextValue(up, sd_acc >= self.step_up),
                    NextValue(down, sd_acc < 0),
                ).Else(
                    NextValue(up, sd_acc > 0),
                    NextValue(down, sd_acc <= -self.step_down),
                ),
                NextState('T1'),
            )
        fsm.act('T1',
                If(up,
                    NextValue(self.shift, 1),
                    NextValue(self.sign, 0),
                    NextValue(err, err - self.step_up),
                    NextValue(sd_acc, sd_acc - self.step_up),
                ),
                If(down,
                    NextValue(self.shift, 1),
                    NextValue(self.sign, 1),
                    NextValue(err, err + self.step_down),
                    NextValue(sd_acc, sd_acc + self.step_down),
                ),
                NextState('T2'),
            )
        fsm.act('T2',
                NextValue(self.shift, 0),
                NextValue(err, err + self.rate),
                If(self.sigmadelta_en,
                    NextValue(sd_acc, sd_acc + err),
                ).Else(
                    NextValue(sd_acc, err),
                ),
                
                NextValue(wait12, wait_time - 4),
                NextState('WAIT'),
            )
        fsm.act('WAIT',
                NextValue(wait12, wait12 - 1),
                If(wait12 == 0,
                    NextState('T0'),
                ),
            )

def sim(sd=True):
    from migen.sim import run_simulation

    dut = SigmaDeltaPSGen(8, 24, 12)

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
        yield dut.sigmadelta_en.eq(sd)
        #yield dut.step_up.eq(nl[i%len(nl)])
        #yield dut.step_down.eq(nl[(i-1)%len(nl)])
        for _ in range(10000):
            yield
            d = (-1)**(yield dut.sign)
            if (yield dut.shift):
                phi += nl[(it-(yield dut.sign))%len(nl)] * d
                it += d
            if (yield dut.lut_shift):
                i += d
                #yield dut.step_up.eq(nl[i%len(nl)])
                #yield dut.step_down.eq(nl[(i-1)%len(nl)])
            a.append(phi)
        open(f'phase{'_sd' if sd else ''}.sim','w').write(str(a))

    
    run_simulation(dut, case1(), vcd_name=f'sim{'_sd'if sd else''}.vcd')
