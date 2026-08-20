## DDMTD isolated design for qualifying the phase detector

This repository provides a gateware for synthesizing an Amaranth implementation
of the <a href="https://white-rabbit.web.cern.ch/documents/White_Rabbit_Clock_Characteristics.pdf">DDMTD</a> for the Digilent Cmod-A7 board as described at
https://github.com/oscimp/amaranth_twstft/tree/main/pcb/cmodA7_twtft

This PCB includes one comparator converting the incoming clock signal to a square
wave (to pin 46), so that a second external comparator is needed to clock the second SMA 
located after the one connected to the SAW filter (pin 36). The DDMTD phase comparator 
output is found on the SMA between the two clock inputs (pin 42). The output can
be fed to a phase noise analyzer or oscilloscope for statistical analysis of the
DDMTD output.
