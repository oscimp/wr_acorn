from amaranth import ClockDomain, ClockSignal, DomainRenamer, Elaboratable, Instance, Module, ResetSignal, Signal
from amaranth.lib.fifo import SyncFIFO
from amaranth.lib.cdc import ResetSynchronizer
from amaranth.lib.wiring import Component, In, Out
from amaranth.build import Resource, Subsignal, Pins, Attrs
from amaranth_stdio.serial import AsyncSerial, AsyncSerialRX, Parity

from ddmtd.ddmtd import DDMTD

class TopDemoDDMTD(Component):
    def __init__(self):
        super().__init__({
            'clk_a': In(1),
            'clk_b': In(1),
            'clk_dmtd': In(1),
            'tx': Out(1),
            })

    def elaborate(self, platform):
        m = Module()
        m.domains.sync = ClockDomain('sync')

        if False:
            mmcm1_feedback = Signal()
            mmcm1_locked = Signal()
            mmcm1_out = Signal()
            m.submodules.mmcm1 = Instance(
                    'MMCME2_ADV',
                    p_CLKFBOUT_MULT_F = 15.875,
                    p_CLKIN1_PERIOD = 1e9/62.5e6,
                    p_COMPENSATION = 'INTERNAL',

                    p_CLKOUT1_DIVIDE = 16,

                    i_CLKIN1 = self.clk_a,
                    o_CLKOUT1 = mmcm1_out,

                    i_CLKFBIN = mmcm1_feedback,
                    o_CLKFBOUT = mmcm1_feedback,
                    o_LOCKED = mmcm1_locked,
                    i_CLKINSEL = 1,
                    )
            mmcm2_feedback = Signal()
            mmcm2_locked = Signal()
            m.submodules.mmcm2 = Instance(
                    'MMCME2_ADV',
                    p_CLKFBOUT_MULT_F = 16.125,
                    p_CLKIN1_PERIOD = 1e9/62.5e6,
                    p_COMPENSATION = 'INTERNAL',

                    p_CLKOUT1_DIVIDE = 16,

                    i_CLKIN1 = mmcm1_out,
                    o_CLKOUT1 = ClockSignal('sync'),

                    i_CLKFBIN = mmcm2_feedback,
                    o_CLKFBOUT = mmcm2_feedback,
                    o_LOCKED = mmcm2_locked,
                    i_CLKINSEL = 1,
                    )
            m.submodules += ResetSynchronizer(~(mmcm1_locked & mmcm2_locked))
        else :
            mmcm_feedback = Signal()
            mmcm_locked = Signal()
            m.submodules.mmcm = Instance(
                    'MMCME2_ADV',
                    p_CLKFBOUT_MULT_F = 16,
                    p_CLKIN1_PERIOD = 1e9/62.5e6,
                    p_COMPENSATION = 'INTERNAL',

                    p_CLKOUT1_DIVIDE = 16,

                    i_CLKIN1 = self.clk_dmtd,
                    o_CLKOUT1 = ClockSignal('sync'),

                    i_CLKFBIN = mmcm_feedback,
                    o_CLKFBOUT = mmcm_feedback,
                    o_LOCKED = mmcm_locked,
                    i_CLKINSEL = 1,
                    )
            m.submodules += ResetSynchronizer(~mmcm_locked)


        m.submodules.ddmtd = ddmtd = DDMTD()
        m.d.comb += ddmtd.clk_a.eq(self.clk_a)
        m.d.comb += ddmtd.clk_b.eq(self.clk_b)

        m.submodules.fifo_phase = fifo_phase = SyncFIFO(
                width = len(ddmtd.phase),
                depth = 16,
                )

        m.d.sync += fifo_phase.w_data.eq(ddmtd.phase)
        m.d.sync += fifo_phase.w_en.eq(ddmtd.new_phase)

        m.submodules.serial = serial = AsyncSerial(
                divisor=round(62.5e6/2e5),
                parity=Parity.NONE)
        m.d.comb += self.tx.eq(serial.tx.o)


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

