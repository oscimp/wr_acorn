from amaranth import ClockDomain, ClockSignal, DomainRenamer, Elaboratable, Instance, Module, ResetSignal, Signal
from amaranth.lib.fifo import SyncFIFO
from amaranth.lib.cdc import ResetSynchronizer
from amaranth.lib.wiring import Component, In
from amaranth.build import Resource, Subsignal, Pins, Attrs
from amaranth_stdio.serial import AsyncSerial, AsyncSerialRX, Parity

from ddmtd.ddmtd import DDMTD
from ddmtd.dco import DCO

class Cmoda7DemoDDMTD(Elaboratable):
    def elaborate(self, platform):
        m = Module()
        m.domains.sync = ClockDomain('sync')

        connect = ("gpio",0)
        platform.add_resources([
            Resource('pins', 0,
                Subsignal('clk_a', Pins('46',conn=connect, dir='i')),
                Subsignal('clk_b', Pins('42',conn=connect, dir='o')),
                Subsignal('clk_dmtd', Pins('36',conn=connect, dir='i')),
                #Subsignal('dbg0', Pins('36',conn=connect, dir='o')),
                Subsignal('out70', Pins('31',conn=connect, dir='o')),
                Subsignal('dbg1', Pins('1',conn=connect, dir='o')),
                Subsignal('dbg2', Pins('3',conn=connect, dir='o')),
                Subsignal('dbg3', Pins('5',conn=connect, dir='o')),
                Subsignal('dbg4', Pins('7',conn=connect, dir='o')),
                Subsignal('dbg5', Pins('9',conn=connect, dir='o')),
                Subsignal('dbg6', Pins('11',conn=connect, dir='o')),
                Attrs(IOSTANDARD="LVCMOS33")
            ),])
        platform.add_resources([
            Resource('dbg', 0,
                Subsignal('dbg0', Pins('36',conn=connect, dir='o')),
                Subsignal('dbg1', Pins('42',conn=connect, dir='o')),
                Attrs(IOSTANDARD="LVCMOS33")
            ),])

        gpio = platform.request('pins', 0)
        clk_b = Signal()
        #m.d.comb += clk_b.eq(gpio.clk_b.i)

        clk_a = Signal()
        m.domains.ctrl = ClockDomain('ctrl')
        #m.submodules.dco = dco = DCO(
        #        f_clk_in = 70e6,
        #        mult_mmcm = 16,
        #        div_mmcm = 16,
        #        cw_size = 20,
        #        )
        #m.d.comb += dco.ctrl_word.eq(00)
        #m.d.comb += dco.clk_in.eq(gpio.clk_a.i)
        ##m.d.comb += clk_b.eq(gpio.clk_b.i)
        ##m.d.comb += clk_a.eq(dco.clk_out)
        m.submodules += Instance('BUFG',
                                 i_I = gpio.clk_a.i,
                                 o_O = clk_a,
                                 )
        #m.d.comb += gpio.out70.o.eq(ClockSignal('sync'))
        platform.add_clock_constraint(clk_a, int(70e6))
        platform.add_clock_constraint(clk_b, int(70e6))
        
        clk_c = Signal()
        m.submodules += Instance('BUFG',
                                 i_I = gpio.clk_dmtd.i,
                                 o_O = clk_c,
                                 )
        platform.add_clock_constraint(clk_c, int(70e6))

        if True: # double pll
            mmcm1_feedback = Signal()
            mmcm1_locked = Signal()
            mmcm1_out = Signal()
            m.submodules.mmcm1 = Instance(
                    'MMCME2_ADV',
                    p_CLKFBOUT_MULT_F = 16,
                    p_CLKIN1_PERIOD = 1e9/70e6,
                    p_COMPENSATION = 'INTERNAL',

                    p_CLKOUT0_DIVIDE_F = 16.125,

                    i_CLKIN1 = clk_a,
                    o_CLKOUT0 = mmcm1_out,

                    i_CLKFBIN = mmcm1_feedback,
                    o_CLKFBOUT = mmcm1_feedback,
                    o_LOCKED = mmcm1_locked,
                    i_CLKINSEL = 1,
                    )
            mmcm2_feedback = Signal()
            mmcm2_locked = Signal()
            m.submodules.mmcm2 = Instance(
                    'MMCME2_ADV',
                    p_CLKFBOUT_MULT_F = 16,
                    p_CLKIN1_PERIOD = 1e9/70e6,
                    p_COMPENSATION = 'INTERNAL',

                    p_CLKOUT0_DIVIDE_F = 15.875,

                    i_CLKIN1 = mmcm1_out,
                    o_CLKOUT0 = ClockSignal('sync'),

                    i_CLKFBIN = mmcm2_feedback,
                    o_CLKFBOUT = mmcm2_feedback,
                    o_LOCKED = mmcm2_locked,
                    i_CLKINSEL = 1,
                    )
            m.submodules += ResetSynchronizer(~(mmcm1_locked & mmcm2_locked))
        elif False: # ext dmtd clk
            m.d.comb += ClockSignal('sync').eq(clk_c)
        else: # MMCM PS clk
            m.domains.ctrl = ClockDomain()
            m.submodules.dco = dco = DCO(
                    f_clk_in = 70e6,
                    mult_mmcm = 16,
                    div_mmcm = 16,
                    cw_size = 20,
                    )
            m.d.comb += dco.ctrl_word.eq(104)
            m.d.comb += dco.clk_in.eq(clk_a)
            m.d.comb += clk_b.eq(dco.clk_out)
            m.d.comb += gpio.clk_dmtd_out.o.eq(dco.clk_out)
            m.submodules += ResetSynchronizer(~dco.locked)


        m.d.comb += gpio.dbg1.o.eq(ClockSignal('sync'))
        m.d.comb += gpio.dbg3.o.eq(ResetSignal('sync'))


        m.submodules.ddmtd = ddmtd = DDMTD()
        m.d.comb += ddmtd.clk_a.eq(clk_a)
        m.d.comb += ddmtd.clk_b.eq(clk_c)

        m.submodules.fifo_phase = fifo_phase = SyncFIFO(
                width = len(ddmtd.phase),
                depth = 16,
                )

        m.d.sync += fifo_phase.w_data.eq(ddmtd.phase)
        m.d.sync += fifo_phase.w_en.eq(ddmtd.new_phase)
        m.d.comb += gpio.dbg2.o.eq(ddmtd.new_phase)
        

        m.d.comb += gpio.clk_b.o.eq(ddmtd.raw_b)
        beat_cnt = Signal(14)
        m.d.sync += beat_cnt.eq(beat_cnt + 1)
        m.d.comb += gpio.dbg5.o.eq(beat_cnt == 0)

        m.submodules.serial = serial = AsyncSerial(
                divisor=round(70e6/2e6),
                parity=Parity.NONE,
                pins=platform.request('uart'))


        m.d.sync += serial.tx.ack.eq(False)
        with m.FSM(reset='WAIT_PHASE') as fsm:
            def send_reg(state: str, reg: Signal, next_state:str='WAIT'):
                for i in range(0, len(reg), 8):
                    name = state if i == 0 else f'__{state}__{i}'
                    name_next = (f'__{state}__{i+8}'
                                 if i < len(reg) - 8 else
                                 next_state)
                    with m.State(name):
                        with m.If(serial.tx.rdy & ~serial.tx.ack):
                            m.d.sync += serial.tx.ack.eq(True)
                            m.d.sync += serial.tx.data.eq(reg[i:i+8])
                            m.next = name_next
            send_reg('SEND_PHASE', fifo_phase.r_data, 'ACK_PHASE')

            with m.State('WAIT_PHASE'):
                with m.If(fifo_phase.r_rdy):
                    m.next = 'SEND_PHASE'
            with m.State('ACK_PHASE'):
                m.d.comb += fifo_phase.r_en.eq(True)
                m.next = 'WAIT_PHASE'

        return m

