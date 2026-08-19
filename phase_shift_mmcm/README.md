# Qualification and correction of the phase shifts of the MMCM

In the VCXO-less implementation of White Rabbit, the oscillators internal
to the FPGA must be fine tuned to track the reference signal (main oscillator),
and the helper oscillator must track the main oscillator to generate a constant
beatnote.

The MMCMs in the Artix7 FPGA use a phase stepping mechanism: periodic phase
increments induce a phase drift $df=phi/(2\pi\cdot t)$ acting as fine frequency
tuning of the MMCM. However, the phase is not behaving as expected: this directory
provides the tools for mapping phase increments, and correct their unexpected 
behaviour.

See <a href="https://docs.amd.com/v/u/en-US/xapp589-VCXO">Xilinx application note XAPP589</a>
for their PICXO implementation.

Wherever a "Phase Station" is referred to, the instrument is the 
<a href="https://www.miles.io/PhaseStation_53100A_user_manual.pdf">Microchip 53100A</a>
from John Miles.
