# Phase shift MMCM demo on CMODA7

This directory contains a demonstration of fine frequency tuning using phase-shifted MMCMs with two phase-noise reductions techniques: sigmadelta noise-shaping and step-size linearization.

## Build and Flash the gateware

To build the gateware you need LiteX+Migen and Vivado configured in the environement, then:
```
./digilent_cmod_a7.py --build
```
or
```
./digilent_cmod_a7.py --build --calib-file normalized_step_sizes.txt
```

And then flash with:
```
openFPGALoader -b cmoda7_35t -f --freq 30e6 -m build/digilent_cmod_a7/gateware/digilent_cmod_a7.bin
```

## Using the demo

The demo gateware needs an input reference clock at 100 MHz on pin `j2:21`, and will output the tuned clock on pin `j2:11` at 62.5 MHz + programmable offset.
The runtime configuration is done via the serial port of the embeded riscv by writing to configuration registers with the commands `mem_write <addr> <val>` and `mem_read <addr>`.


### Configuration registers

To know the addresses of these registers you should fetch them after build with:
```
$ cat build/digilent_cmod_a7/csr.csv | grep dco
csr_register,main_dco_rate,0xf0002000,1,rw
csr_register,main_dco_csr,0xf0002004,1,rw
csr_register,main_dco_stat,0xf0002008,1,ro
```

- `main_dco_rate` is the 24 bits **signed** frequency tuning word, the frequency control is linear with a granularity of 100e6/12/2^24/56/16 ~= 2.2 mHz.

- `main_dco_csr` is a bitfield controling the logic:
    - `main_dco_csr[0]` : RESET, resets all the control logic (except the values of the linearization LUT) and the MMCM's phase position to their deterministic initial state.
    - `main_dco_csr[1]` : SIGMADELTA\_EN, enables the sigmadelta noise-shaping.
    - `main_dco_csr[2]` : LINEARIZATION\_EN, enables the step-size linearization.
    - `main_dco_csr[3]` : START\_CALIB, starts the auto-calibration procedure after a boot or reset, then starts the phase-shift operation, WARNING : it has no effect once the DCO is running, to re-do a calibration you must first RESET.
    - `main_dco_csr[4]` : START\_NO\_CALIB, starts the phase-shift operation immediatly bypassing auto-calibration, this allow to use the manual calibration file specified at synthesis, WARNING : it has no effect once the DCO is running.

- `main_dco_stat` is a bitfield containing information about the DCO current state:
    - `main_dco_stat[0]` : CALIB\_DONE, asserted once the auto-calibration procedure is complete.
    - `main_dco_stat[1]` : DOING\_CALIB, asserted while the auto-calibration procedure is running.
    - `main_dco_stat[16:32]` : DMTD\_TAG, the latest DMTD phase-tag of the tuned clock measured by the embeded DMTD (big-endian)

### Auto-Calibration

1) Reset the logic :
```
litex> mem_write 0xf0002004 1
```

2) Launch the auto-calibration procedure :
```
litex> mem_write 0xf0002004 8
```

3) Wait until `main_dco_stat[0]` is asserted, this should take about 5 minutes. And then it's done.

### Manual Calibration

To create a calibration file you need to measure the phase steps with an external phase-meter such as the 
<a href="https://www.miles.io/PhaseStation_53100A_user_manual.pdf">phase station</a>.

1) Reset the logic, set a null command word (no frequency offset = no phase shifts) and start the DCO without calibration nor sigmadelta :
```
litex> mem_write 0xf0002004 1
litex> mem_write 0xf0002000 0
litex> mem_write 0xf0002004 16
```

2) Start the acquistion on the phase station with a maximum of phase points per seconds (1000 on the phase station) and wait a few seconds get the base phase

3) Set a very small frequency offset so the phase steps are clearly visible on the phase station.
```
litex> mem_write 0xf0002000 5
```

4) Wait at least until the total phase shift reachs 2 ns in order to get an observation of each 112 phase steps, longer acquisitions allow to get more observations per step and to reject some of the low frequency drift.

5) <a href="analyze_tim.m">Process the acquisition</a> to extract the 112 sizes of phase steps and normalize them so that their mean value is 1 (the sum of the normalized steps has to be 112), and save them in a text file separated by newlines, spaces or tabs.

Once you have created this calibration file, you can use it as the default calibration for the next synthesis by passing it via the `--calib-file` argument :
```
./digilent_cmod_a7.py --build --calib-file normalized_step_sizes.txt
```

## Correction application

For using the features, mask 16 (enable) with 4 (phase linearization) and  2 (sigma-delta correction):

Calibrated phase jump correction 
```
mem_write 0xf0002004 20
```
Sigma-Delta
```
mem_write 0xf0002004 18
```
Linearization and Sigma-Delta
```
mem_write 0xf0002004 22
```
