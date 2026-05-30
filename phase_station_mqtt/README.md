# Controlling the Microchip 53100A Phase Noise Analyzer (aka Phase Station) for qualifying the White Rabbit link

## Principle

The Microchip 53100A Phase Station is provided with a javascript interpreter to automate
data acquisition. Using the blocking MQTT Publish/Subscribe calls, the acquisition is
synchronized with a Python script assessing the state of the White Rabbit node and
controlling the start of data collection. The Phase Station stores the records on the
MS-Windows hard disk for post-processing. A MQTT server (``broker``) is assumed to be
accessible on the same subnet than the Phase Station and the PC controlling the White
Rabbit board, possibly on the same latter GNU/Linux computer. In our examples, the
broker is running on a computer with IP 192.168.1.170.

<img src="architecture.png">

## Setup

From the MQTT <a href="https://mosquitto.org/download/">repository</a> download
the MS-Windows version of Mosquitto clients and install on the MS-Windows computer
controlling the phase station since we are using a ping-pong scheme to sequence the
Phase Station acquisition and White Rabbit node behaviour control.

## Using the phase station for automated measurements with Mosquitto MQTT

The 53100A Phase Noise Analyzer allows the cration of custom Javascript scripts runnable 
from the TimeLab GUI to automate the opperation of the phase station. This repository
contains an example of automated repeated measurement, synchronized via MQTT with the 
DUT's host computer.

In this example, we repeat absolute phase measurements of an auxiliary White Rabbit clock, 
and relock the White Rabbit softPLL between each aquisition. The phase station is 
controled by <a href="phase_station_script_example.js">phase_station_script_example.js</a>
whose task is to launch and save acquisitions, while the White Rabbit device is controlled 
by <a href="wr_host_script_example.py">wr_host_script_example.py</a> whose task is to 
reset and relock the softPLL.

The two script are synchronized via MQTT and their parallel execution can be sumarized as:

|   | phase station control | white rabbit control |
|:-:|:---------------------:|:--------------------:|
| 1 |       wait MQTT       |    relock softPLL    |
| 2 |        get MQTT       |       send MQTT      |
| 3 |   acquire phase data  |       wait MQTT      |
| 4 |       send MQTT       |       get MQTT       |
| 5 |     loop to step 1    |    loop to step 1    |


## The 53100A Phase Noise Analyzer is not made for absolute phase measurments

The phase station is a *noise* analyzer and does not claim the ability to perform 
absolute phase measurements, and can introduce offset error of $\pm 1.3$ ns and 1.5 ps. 
This behavor is descibed in <a href="phase_station_indeterminism_quirks.pdf">phase_station_indeterminism_quirks.pdf</a>.
