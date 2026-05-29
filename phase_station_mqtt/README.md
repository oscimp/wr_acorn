## Using the phase station for automated measurements with Mosquitto MQTT

The 53100A Phase Noise Analyzer allows the cration of customs scripts runnables from the TimeLab gui to automate the opperation of the phase station.
This directory contains an example of automated repeated measurement, synchronized via MQTT with the DUT's host computer.

In this example we repeat absolute phase measurements of an auxiliary white rabbit clock, and relock the white rabbit softpll between each aquisition.
The phase station is controled by `phase_station_script_example.js` who's task is to launch and save acqisitions, and the wr device is controled by `wr_host_script_example.py` who's task is to reset and relock the softpll.

The two script are synchronized via MQTT and their parallel execution can be sumarized as:

|   | phase station control | white rabbit control |
|:-:|:---------------------:|:--------------------:|
| 1 |       wait MQTT       |    relock softpll    |
| 2 |        get MQTT       |       send MQTT      |
| 3 |   acquire phase data  |       wait MQTT      |
| 4 |       send MQTT       |       get MQTT       |
| 5 |     loop to step 1    |    loop to step 1    |


### The 53100A Phase Noise Analyzer is not made for absolute phase measurments

The phase station is a *noise* analyzer and doesn't claim the ability to perform absolute phase measurements, and can introduce offset error of +/- 1.3 ns and 1.5 ps. This behavor is descibed in `phase_station_indeterminism_quirks.pdf`.
