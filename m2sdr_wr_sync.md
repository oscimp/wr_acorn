# clocking the ad9361 from white rabbit

This step allow to syntonize multiples m2sdr together using white rabbit. Note that the sdr will not be syntonized on white-rabbit because the ad9361's frac-pll can't synthesize some frequencies exactly, however multiple ad9361 clocked from the same source (white rabbit clock) with the same configuration will be syntonized together.

## configuration

On the m2sdr, the ad9361 is clocked from an si5351 which exist in three versions A, B and C, only the version C support a CMOS clock input.

The si5351c `CLK_IN` pin is connected to pin `W22` of the FPGA named `si5351/ssen_clkin` in litex. Outputing a white rabbit clock on this pin and configuring the si5351 registers to use the `CLK_IN` as reference will result in the ad9361 syntonization.

This can be done with :

```
./m2sdr_rf -sync white-rabbit [other arguments for the desired rf config]
```

example :
```
./m2sdr_rf -sync white-rabbit -rx_freq 70000000 -rx_gain 20 -samplerate 10000000
```

## syntonization verification

To check the syntonisation the most strait-forward way is to split a sinusoidal signal to two m2sdrs RX1 ports and record it with `m2sdr_record`.
Then the ratio of the IQ of one file by the other should be constant.

Example with a 70.5 MHz sin wave,

```bash
./m2sdr_rf -sync white-rabbit -rx_freq 70000000 -rx_gain 20 -samplerate 10000000 -c 0 # configure m2sdr0
./m2sdr_rf -sync white-rabbit -rx_freq 70000000 -rx_gain 20 -samplerate 10000000 -c 1 # configure m2sdr1

./m2sdr_record -c 0 /tmp/a.bin 10000000 & ./m2sdr_record -c 1 /tmp/b.bin 10000000 # record the sin wave with both m2sdr
```

Then analyse the phase rotation :
```py
import numpy as np
from matplotlib import pyplot as plt
a = np.fromfile('/tmp/a.bin', dtype='int16')
b = np.fromfile('/tmp/b.bin', dtype='int16')
a = a[::4] + 1j * a[1::4] # the IQ sin wave recorded by m2sdr0
b = b[::4] + 1j * b[1::4] # the IQ sin wave recorded by m2sdr1
plt.plot(np.angle(a / b)) # plot the phase difference, expecting a constant
plt.show()
```

When the srd are synthonized, their phase difference is a constant, as examplified in the plot below :

<img src='pictures/phase_diff_synth.png'>

# DMA synchronisation on PPS

# ADC synchronisation

## hardware mod for SYNC\_IN pin

## si5351-c passthrough

## checking and fixing timing constraint on SYNC\_IN pin

## synchronisation verification
