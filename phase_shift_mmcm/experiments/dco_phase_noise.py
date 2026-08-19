import numpy as np
from scipy.signal import welch
from matplotlib import pyplot as plt

fb = 3814

def trace(filename, legend='', offset=0):
    d = np.fromfile(filename, dtype=np.uint16)
    #plt.plot(d)
    d = (d+offset) % 2**14
    d = d[2150:] * 2 * np.pi / 2**14
    d = d - np.average(d)
    f, psd = welch(d, fb)
    plt.plot(f, 10*np.log10(psd), label=legend)
    #plt.figure()
    s = len(d)

    #plt.plot(list(i/fb for i in range(len(d))),d)

def traceft(filename, legend='', offset=0):
    d = np.fromfile(filename, dtype=np.uint16)
    d = (d+offset) % 2**14
    d = d[2150:] * 2 * np.pi / 2**14
    d = d - np.average(d)
    s = len(d)
    plt.plot([fb * i/s/2 for i in range(-s, s, 2)], np.abs(np.fft.fftshift(np.fft.fft(d))), label=legend)


#trace('dmtd_wr2', 'WR softpll clk (mmcm ps vco 1 GHz)', offset=2**13)
trace('dmtd_wr', 'WR softpll clk (mmcm ps vco 1.5 GHz)')
#trace('dmtd_wr1.25G', 'WR softpll clk (mmcm ps vco 1.25 GHz)')
trace('dmtd_mmcm1.5G', 'MMCM phase shifts (vco 1.5 GHz)')
trace('dmtd_pll', 'double frac pll')
trace('dmtd_sma', 'SMA100A')
#trace('dmtd_mmcm', 'MMCM phase shifts (vco 1 GHz)')
plt.xscale('log')
plt.xlabel('frequency offset (Hz)')
plt.ylabel('PSD (dBrad²/Hz)')
plt.grid(True, which="both")
plt.legend()
plt.show()
