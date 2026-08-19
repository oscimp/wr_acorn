#!/usr/bin/env python3

#
# This file is part of LiteX-Boards.
#
# Copyright (c) 2021 Michael T. Mayers <michael@tweakoz.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.genlib.resetsync import *

from litex.gen import *


from litex_boards.platforms import digilent_cmod_a7

from litex.soc.cores.clock import *
from litex.soc.integration.soc import *
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.builder import *
from litex.soc.cores.led import LedChaser
from litex.soc.interconnect import wishbone

from litex.soc.integration.soc import colorer
from litex.build.generic_platform import IOStandard, Pins

from gateware.self_calib_picxo_wr_clock_assembly import WRClocking 

# CRG ----------------------------------------------------------------------------------------------

class _CRG(LiteXModule):
    def __init__(self, platform, sys_clk_freq):
        self.rst    = Signal()
        self.cd_sys = ClockDomain()

        # # #

        # Clk/Rst.
        clk12 = platform.request("clk12")
        rst   = platform.request("cpu_reset")

        # PLL.
        self.pll = pll = S7MMCM(speedgrade=-1)
        self.comb += pll.reset.eq(rst | self.rst)
        pll.register_clkin(clk12, 12e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        platform.add_false_path_constraints(self.cd_sys.clk, pll.clkin) # Ignore sys_clk to pll.clkin path created by SoC's rst.

# AsyncSRAM ------------------------------------------------------------------------------------------

class AsyncSRAM(LiteXModule):
    def __init__(self, platform, size):
        addr_width = size//8
        data_width = 8
        self.bus = wishbone.Interface(data_width=data_width,adr_width=addr_width)
        issiram = platform.request("issiram")
        addr = issiram.addr
        data = issiram.data
        wen = issiram.wen
        cen = issiram.cen
        oe = issiram.oe
        ########################
        tristate_data = TSTriple(data_width)
        self.specials += tristate_data.get_tristate(data)
        ########################
        chip_ena = self.bus.cyc & self.bus.stb & self.bus.sel[0]
        write_ena = (chip_ena & self.bus.we)
        ########################
        # external write enable,
        # external chip enable,
        # internal tristate write enable
        ########################
        self.comb += [
            cen.eq(~chip_ena),
            wen.eq(~write_ena),
            tristate_data.oe.eq(write_ena),
            oe.eq(tristate_data.oe),
        ]
        ########################
        # address and data
        ########################
        self.comb += [
            addr.eq(self.bus.adr[:addr_width]),
            self.bus.dat_r.eq(tristate_data.i[:data_width]),
            tristate_data.o.eq(self.bus.dat_w[:data_width])
        ]
        ########################
        # generate ack
        ########################
        self.sync += [
            self.bus.ack.eq(self.bus.cyc & self.bus.stb & ~self.bus.ack),
        ]
        ########################


def addAsyncSram(soc, platform, name, origin, size):
    ram_bus = wishbone.Interface(data_width=soc.bus.data_width)
    ram     = AsyncSRAM(platform,size)
    soc.bus.add_slave(name, ram.bus, SoCRegion(origin=origin, size=size, mode="rw"))
    soc.check_if_exists(name)
    soc.logger.info("ISSIRAM {} {} {}.".format(
        colorer(name),
        colorer("added", color="green"),
        soc.bus.regions[name]))
    setattr(soc.submodules, name, ram)

# BaseSoC ------------------------------------------------------------------------------------------

class BaseSoC(SoCCore):
    def __init__(self,  variant="a7-35",
        toolchain       = "vivado",
        sys_clk_freq    = 100e6,
        with_spi_flash  = False,
        **kwargs):

        platform = digilent_cmod_a7.Platform(variant=variant, toolchain=toolchain)

        # CRG --------------------------------------------------------------------------------------
        self.crg = _CRG(platform, sys_clk_freq)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, sys_clk_freq, ident="LiteX SoC on Digilent CmodA7", **kwargs)

        # Async RAM --------------------------------------------------------------------------------
        addAsyncSram(self,platform,"main_ram", 0x40000000, 512 * KILOBYTE)

        # SPI Flash --------------------------------------------------------------------------------
        if with_spi_flash:
            from litespi.modules import MX25U3235F
            from litespi.opcodes import SpiNorFlashOpCodes as Codes
            self.add_spi_flash(mode="4x", module=MX25U3235F(Codes.READ_1_1_4), with_master=True)

        # DCO
        ####################

        frac_size = 24
        int_size = 8

        platform.add_extension([
            ('clk_in',  0, Pins('j2:21'), IOStandard('LVCMOS33')),
            ('clk_out', 0, Pins('j2:11'), IOStandard('LVCMOS33')),
            ('dbg',     0, Pins('j2:17'), IOStandard('LVCMOS33')),
        ])

        clk_in = Signal()
        clk_out = Signal()
        self.comb += clk_in.eq(platform.request('clk_in'))
        self.comb += platform.request('clk_out').eq(clk_out)
        platform.add_period_constraint(clk_in, 1e9/100e6)
        
        self.dco_rate = CSRStorage(size=frac_size)
        self.dco_csr = CSRStorage(fields=[
            CSRField("reset", size=1, offset=0),
            CSRField("sigmadelta_en", size=1, offset=1),
            CSRField("nonlin_en", size=1, offset=2),
            CSRField("start_calib", size=1, offset=3),
            CSRField("start_no_calib", size=1, offset=4),
        ])
        
        self.dco_stat = CSRStatus(fields=[
            CSRField("calib_done", size=1, offset=0),
            CSRField("doing_calib", size=1, offset=1),
            CSRField("dmtd_tag", size=16, offset=16),
        ])

        self.clocking = WRClocking(platform, frac_size=frac_size, int_size=int_size)
        
        self.comb += [
                self.clocking.clk100_in.eq(clk_in),
                clk_out.eq(self.clocking.tunned_clk),

                platform.request('dbg').eq(self.clocking.sigmadelta.dither_en),

                self.clocking.freq_cmd.eq(self.dco_rate.storage),
                self.clocking.reset.eq(self.dco_csr.fields.reset),
                self.clocking.sigmadelta_en.eq(self.dco_csr.fields.sigmadelta_en),
                self.clocking.linearize_en.eq(self.dco_csr.fields.nonlin_en),
                self.clocking.start_calib.eq(self.dco_csr.fields.start_calib),
                self.clocking.start_no_calib.eq(self.dco_csr.fields.start_no_calib),
                
                self.dco_stat.fields.calib_done.eq(self.clocking.calib_done),
                self.dco_stat.fields.doing_calib.eq(self.clocking.doing_calib),
                self.dco_stat.fields.dmtd_tag.eq(self.clocking.calib.tag),
                ]




# Build --------------------------------------------------------------------------------------------

def main():
    from litex.build.parser import LiteXArgumentParser
    parser = LiteXArgumentParser(platform=digilent_cmod_a7.Platform, description="LiteX SoC on CMOD A7.")
    parser.add_target_argument("--flash",          action="store_true",      help="Flash bitstream.")
    parser.add_target_argument("--variant",        default="a7-35",          help="Board variant (a7-35 or a7-100).")
    parser.add_target_argument("--sys-clk-freq",   default=48e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--with-spi-flash", action="store_true",      help="Enable memory-mapped SPI flash.")

    args = parser.parse_args()

    soc = BaseSoC(
        variant        = args.variant,
        toolchain      = args.toolchain,
        sys_clk_freq   = args.sys_clk_freq,
        with_spi_flash = args.with_spi_flash,
        **parser.soc_argdict
    )

    builder_argd = parser.builder_argdict

    builder = Builder(soc, **builder_argd)
    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

    if args.flash:
        prog = soc.platform.create_programmer()
        prog.flash(0, builder.get_bitstream_filename(mode="flash"))

if __name__ == "__main__":
    main()

class BaseSoC_SIM(LiteXModule):
    def __init__(self,
                 int_size=8,
                 frac_size=24,
                 dco_rate=775680,
                 dco_dither_en=1,
                 dco_nonlin_en=1,
                 ):
        from gateware.sigmadelta import SigmaDeltaPSGen
        from gateware.nonlin_lut import NonLinearityLUT, lut_from_trace

        self.sigmadelta = SigmaDeltaPSGen(int_size=int_size, frac_size=frac_size)
        self.sd_lut = NonLinearityLUT(lut=lut_from_trace('non_linearities_rec/calib_X1Y0.tim', inv=False), int_size=int_size, frac_size=frac_size)

        self.comb += [
                self.sigmadelta.rate.eq(dco_rate),
                self.sigmadelta.dither_en.eq(dco_dither_en),
                self.sigmadelta.step_up.eq(
                    Mux(dco_nonlin_en,
                        self.sd_lut.step_up,
                        1 << frac_size,
                    )),
                self.sigmadelta.step_down.eq(
                    Mux(dco_nonlin_en,
                        self.sd_lut.step_down,
                        1 << frac_size,
                    )),
                self.sd_lut.lut_shift.eq(self.sigmadelta.lut_shift),
                self.sd_lut.sign.eq(self.sigmadelta.sign),
                ]

def sim(sd, nl, n=100000):
    from migen.sim import run_simulation

    dut = BaseSoC_SIM(dco_dither_en=sd, dco_nonlin_en=nl)

    def run():
        l = [None] * n
        p = 0
        pl = 0
        for i in range(n):
            yield
            shift = (yield dut.sigmadelta.shift)
            lut_shift = (yield dut.sigmadelta.lut_shift)
            sign = (yield dut.sigmadelta.sign)
            count = (yield dut.sd_lut.count)
            if shift:
                p += -1 if sign else 1
            if lut_shift:
                pl += -1 if sign else 1
            l[i] = (p, pl, count)
        open(f'phase_sim_{sd}_{nl}.txt', 'w').write(str(l))


    run_simulation(dut, run(), vcd_name=f'sim_{sd}_{nl}.vcd')
