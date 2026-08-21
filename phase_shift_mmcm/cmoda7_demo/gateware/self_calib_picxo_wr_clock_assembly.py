#!/usr/bin/env python3

#

import numpy as np
from migen import *
from migen.genlib.resetsync import *
from migen.genlib.cdc import *

from litex.gen import *


from gateware.sigmadelta import SigmaDeltaPSGen
from gateware.nonlin_lut import *
from gateware.dmtd import *
from gateware.pll_dmtd_clk import *
from gateware.self_calib_ctrl import *


# BaseSoC ------------------------------------------------------------------------------------------

class WRClocking(LiteXModule):
    def __init__(self, platform, calib_file=None, int_size=8, frac_size=24, n_pos=112):
        self.clk100_in = Signal()
        
        self.tunned_clk = Signal()
        self.dmtd_clk = Signal()

        self.freq_cmd = Signal(int_size + frac_size)

        self.linearize_en = Signal()
        self.sigmadelta_en = Signal()

        self.start_calib = Signal()
        self.start_no_calib = Signal()
        self.calib_done = Signal()
        self.doing_calib = Signal()


        ####################

        tag_size = 14
        
        #self.cd_ctrl = ClockDomain()
        self.cd_dmtd = ClockDomain()

        self.reset = Signal()
        
        # tunning MMCM
        mmcm_shift = Signal()
        mmcm_sign = Signal()
        
        unshifted_clk = Signal()

        mmcm_feedback = Signal()
        mmcm_locked = Signal()
        self.specials += Instance("MMCME2_ADV",
            name = 'phase_shift_mmcm',
            p_BANDWIDTH = 'HIGH',
            p_CLKFBOUT_MULT_F    = 10,
            p_DIVCLK_DIVIDE      = 1,
            p_CLKIN1_PERIOD      = 10, # ns
            p_REF_JITTER1        = 0.0,

            # Outputs
            p_CLKOUT0_DIVIDE_F   = 10,
            p_CLKOUT1_DIVIDE     = 16,
            p_CLKOUT2_DIVIDE     = 16,
            
            p_CLKOUT1_USE_FINE_PS = "TRUE",
            #p_CLKFBOUT_USE_FINE_PS = "TRUE",

            #o_CLKOUT0            = ClockSignal('ctrl'),
            o_CLKOUT1            = self.tunned_clk,
            #o_CLKOUT2            = unshifted_clk,

            # phase shift
            i_PSCLK              = ClockSignal('ctrl'),
            i_PSEN               = mmcm_shift,
            i_PSINCDEC           = mmcm_sign,
            #o_PSDONE             = shift_done,

            # config
            i_PWRDWN               = 0,
            i_RST                  = self.reset,
            i_CLKINSEL             = 1,
            i_CLKFBIN              = mmcm_feedback,
            o_CLKFBOUT             = mmcm_feedback,
            i_CLKIN1               = self.clk100_in,
            o_LOCKED               = mmcm_locked,

            # UNUSED
            p_SS_EN                = "FALSE",
        )
        platform.add_platform_command("set_property LOC MMCME2_ADV_X1Y0 [get_cells {{phase_shift_mmcm}}]")
        self.specials += AsyncResetSynchronizer(ClockDomain('ctrl'), self.reset | ~mmcm_locked)

        # phase shift ctrl
        self.sigmadelta = ClockDomainsRenamer('ctrl')(SigmaDeltaPSGen(int_size=int_size, frac_size=frac_size))
        self.cmd_sync = BusSynchronizer(len(self.freq_cmd), 'sys', 'ctrl')
        self.specials += MultiReg(self.sigmadelta_en, self.sigmadelta.sigmadelta_en, 'ctrl')
        self.comb += [
                self.cmd_sync.i.eq(self.freq_cmd),
                ]

        # NL LUT
        self.sd_lut = ClockDomainsRenamer('ctrl')(NonLinearityLUT(
            lut=(np.array(list(map(float, open(calib_file, 'r').read().split()))) if calib_file is not None else None),
            int_size=int_size, frac_size=frac_size, n=n_pos))
        ctrl_linearize_en = Signal()
        self.specials += MultiReg(self.linearize_en, ctrl_linearize_en, 'ctrl')
        self.comb += [
                self.sigmadelta.step_up.eq(
                    Mux(ctrl_linearize_en,
                        self.sd_lut.step_up,
                        1 << frac_size,
                    )),
                self.sigmadelta.step_down.eq(
                    Mux(ctrl_linearize_en,
                        self.sd_lut.step_down,
                        1 << frac_size,
                    )),
                ]

        ## DMTD clock
        #self.dmtd_pll = PLL_DMTD()
        #platform.add_platform_command("set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets main_clocking_dmtd_pll_mmcm1_out]")
        self.comb += [
        #        self.dmtd_pll.clk_in.eq(unshifted_clk),
        #        self.dmtd_clk.eq(self.dmtd_pll.clk_dmtd),
                ClockSignal('dmtd').eq(0),#self.dmtd_clk),
                ]

        # DMTD
    
        self.dmtd = ClockDomainsRenamer('dmtd')(DMTD())

        self.dmtd_tag = BusSynchronizer(tag_size + 1, 'dmtd', 'ctrl')
        self.sync.dmtd += If(self.dmtd.rdy,
                            self.dmtd_tag.i.eq(Cat(1, self.dmtd.tag)),
                          )
        o_ready = Signal()
        self.sync.ctrl += o_ready.eq(self.dmtd_tag.o[0])
        self.dmtd_tag_ack = PulseSynchronizer('ctrl', 'dmtd')
        
        self.sync.dmtd += If(self.dmtd_tag_ack.o,
                            self.dmtd_tag.i[0].eq(0),
                          )

        
        tag = Signal(tag_size)
        tag_rdy = Signal()
        self.comb += [
                self.dmtd.clk_in.eq(self.tunned_clk),
                tag.eq(self.dmtd_tag.o[1:]),
                tag_rdy.eq(o_ready & ~self.dmtd_tag.o[0]),
                self.dmtd_tag_ack.i.eq(o_ready),
                ]

        # Calib ctrl
        self.calib = ClockDomainsRenamer('ctrl')(SelfCalibCtrl(int_size=int_size, frac_size=frac_size, n=n_pos))
        
        self.sync.ctrl += [
            self.calib.tag.eq(tag),
            self.calib.tag_rdy.eq(tag_rdy),
            ]

        # State machine
        ctrl_start_calib = Signal()
        ctrl_start_no_calib = Signal()
        self.specials += MultiReg(self.start_calib, ctrl_start_calib,  'ctrl')
        self.specials += MultiReg(self.start_no_calib, ctrl_start_no_calib,  'ctrl')
        self.fsm = ClockDomainsRenamer('ctrl')(FSM())
        self.fsm.act('START_CALIB',
                If(self.calib.ready & ctrl_start_calib,
                   self.calib.start.eq(1),
                   NextState('CALIB'),
                ),
                If(ctrl_start_no_calib,
                   NextState('RUNNING'),
                ),
            )
        self.fsm.act('CALIB',
                mmcm_shift.eq(self.calib.shift),
                mmcm_sign.eq(self.calib.sign),
                self.sd_lut.lut_shift.eq(self.calib.shift),
                self.sd_lut.sign.eq(self.calib.sign),
                self.sd_lut.write_en.eq(self.calib.we),
                self.sd_lut.write_val.eq(self.calib.val),
                self.doing_calib.eq(1),
                If(self.calib.done,
                   NextState('RUNNING'),
                   NextValue(self.calib_done, 1),
                ),
            )
        self.fsm.act('RUNNING',
                mmcm_shift.eq(self.sigmadelta.shift),
                mmcm_sign.eq(self.sigmadelta.sign),
                self.sd_lut.lut_shift.eq(self.sigmadelta.shift),
                self.sd_lut.sign.eq(self.sigmadelta.sign),
                self.sigmadelta.rate.eq(self.cmd_sync.o),
            )

