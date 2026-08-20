from math import ceil

from amaranth import ClockDomain, ClockSignal, Const, Instance, Module, Mux, ResetSignal, Shape, Signal, signed
from amaranth.lib.wiring import Component, In, Out

class DCO(Component):
    def __init__(self,
                 f_clk_in:int,
                 mult_mmcm:float,
                 div_mmcm:int,
                 cw_size=32):
        super().__init__({
                'clk_in': In(1),
                'clk_out': Out(1),
                'locked': Out(1),
                'reset': In(1),

                'ctrl_clk': Out(1),
                'ctrl_word': In(signed(cw_size)), # fixed point -> <ctrl_word[-1]>.<ctrl_word[:-1]>
            })
        self.f_clk_in = f_clk_in
        self.mult_mmcm = mult_mmcm
        self.div_mmcm = div_mmcm
        self.cw_size = cw_size

    def f_ctrl(self):
        return (self.f_clk_in * self.mult_mmcm)/3

    def elaborate(self, platform):
        m = Module()

        m.d.comb += ClockSignal('ctrl').eq(self.ctrl_clk)
        m.d.comb += ResetSignal('ctrl').eq(self.reset | ~self.locked)

        mmcm_feedback = Signal()
        mmcm_locked = Signal()
        mmcm_out = Signal()
        shift = Signal()
        shift_done = Signal()

        ctrl_word = Signal(self.cw_size)
        ctrl_sign = Signal()

        with m.If(self.ctrl_word >= 0):
            m.d.ctrl += ctrl_word.eq(self.ctrl_word)
            m.d.ctrl += ctrl_sign.eq(False)
        with m.Else():
            m.d.ctrl += ctrl_word.eq(-self.ctrl_word)
            m.d.ctrl += ctrl_sign.eq(True)

        m.submodules.mmcm = Instance("MMCME2_ADV",
            p_BANDWIDTH = 'LOW',
            p_COMPENSATION = 'INTERNAL',
            p_CLKFBOUT_MULT_F    = self.mult_mmcm,
            p_DIVCLK_DIVIDE      = 1,
            p_CLKIN1_PERIOD      = 1e9 / self.f_clk_in,
            p_REF_JITTER1         = 0.0,

            # Outputs
            p_CLKOUT0_DIVIDE_F   = round(8* self.f_clk_in * self.mult_mmcm / 200e6)/8,
            p_CLKOUT1_DIVIDE     = self.div_mmcm,
            p_CLKOUT1_USE_FINE_PS = True,

            o_CLKOUT0            = self.ctrl_clk,
            o_CLKOUT1            = self.clk_out,

            # phase shift
            i_PSCLK              = self.ctrl_clk,
            i_PSEN               = shift,
            i_PSINCDEC           = ctrl_sign,
            o_PSDONE             = shift_done,

            # config
            i_PWRDWN               = 0,
            i_RST                  = self.reset,
            i_CLKINSEL             = 1,
            i_CLKFBIN              = mmcm_feedback,
            o_CLKFBOUT             = mmcm_feedback,
            i_CLKIN1               = self.clk_in,
            o_LOCKED               = self.locked,

            # UNUSED
            p_SS_EN                = "FALSE",
            i_DADDR                = Const(0, 7),
            i_DEN                  = 0,
            i_DI                   = Const(0, 16),
            i_DWE                  = 0,
            i_CLKIN2               = Const(0),
        )

        timer = Signal.like(ctrl_word)
        one = 1 << (len(ctrl_word) - 1)

        m.d.ctrl += timer.eq(timer+ctrl_word)

        with m.FSM(domain='ctrl'):
            with m.State('COUNTING'):
                with m.If(timer >= one):
                    m.d.ctrl += timer.eq(timer - one + ctrl_word)
                    m.next = 'SHIFT'
            with m.State('SHIFT'):
                m.d.ctrl += shift.eq(True)
                m.next = 'SHIFTING'
            with m.State('SHIFTING'):
                m.d.ctrl += shift.eq(False)
                with m.If(shift_done):
                    m.next = 'COUNTING'

        return m
