import numpy as np
from matplotlib import pyplot as plt
import time
import os
from scipy.signal import welch

def get_trace(filename):
    r = open(filename, 'r').read()
    b, r = r.split('TIC ', maxsplit=1)
    r = r.split('\n', maxsplit=1)[1]
    r = r.split(';', maxsplit=1)[0]
    r = r.strip()
    r = r.split()
    r = list(map(float, r))
    
    return np.array(r)


def plot_phase_noise(ax, phase, fs, nperseg=16384, label=None, **plot_kwargs):
    """
    Plot phase noise PSD (dBrad²/Hz) on an existing matplotlib axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axis to plot on.
    phase : ndarray
        Phase samples in radians.
    fs : float
        Sampling frequency in Hz.
    nperseg : int
        Welch segment length.
    label : str, optional
        Curve label.
    **plot_kwargs
        Additional arguments passed to ax.plot().

    Returns
    -------
    f : ndarray
        Frequency offset (Hz).
    L : ndarray
        Phase noise PSD (dBrad²/Hz).
    """

    phase = np.asarray(phase)
    phase = phase - np.mean(phase)

    f, psd = welch(
        phase,
        fs=fs,
        window="hann",
        nperseg=min(nperseg, len(phase)),
        detrend=False,
        scaling="density",
        return_onesided=True,
    )

    # Convert rad²/Hz -> dBrad²/Hz
    L = 10 * np.log10(psd)

    # Skip DC
    ax.plot(f[1:], L[1:], label=label, **plot_kwargs)

    ax.set_xscale("log")
    ax.set_xlabel("Offset frequency (Hz)")
    ax.set_ylabel("Phase noise (dBrad²/Hz)")
    ax.grid(True, which="both")

    return f, L

def plot_cmp_opt():
    fig, ax = plt.subplots()
    fs = 1000

    plot_phase_noise(ax, get_trace('mmcm_opts_2007/mmcm.tim'), fs, label="MMCM simple")
    plot_phase_noise(ax, get_trace('mmcm_opts_2007/mmcm_sd.tim'), fs, label="MMCM sigmadelta")
    plot_phase_noise(ax, get_trace('mmcm_opts_2007/mmcm_nl.tim'), fs, label="MMCM linearized")
    plot_phase_noise(ax, get_trace('mmcm_opts_2007/mmcm_nl_sd.tim'), fs, label="MMCM linearized sigmadelta")

    ax.legend()
    plt.show()
