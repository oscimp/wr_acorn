import numpy as np
from scipy.signal import welch
from matplotlib import pyplot as plt

# the goal of this simulation is to compute the minimum phase noise to be expected at the output of a phase shifted mmcm with the best possible asservisment

def sim(sim_time=.1, # s
        dac_bits = 16,
        vco_f = 1.5e9, # Hz
        ps_f = 200e6, # Hz
        out_f = 62.5e6, # Hz
        ratio = 2**14/(2**14-1),
        dither = False,
        sample_div = 1):

    ps_size = 1/vco_f/56
    ps_size_rad = ps_size/(1/out_f) *2 * np.pi
    ps_rate = (ratio*vco_f - vco_f) * 56

    ideal_cmd = 8960 # ps_rate / ps_f * 2**(dac_bits + 3)
    if not dither: # exactly synthesizable frequency
        ratio = (round(ideal_cmd) / 2**(dac_bits + 3) * ps_f / 56 + vco_f) / vco_f
        ps_rate = (ratio*vco_f - vco_f) * 56
        ideal_cmd = round(ps_rate / ps_f * 2**(dac_bits + 3)) # should already be an integer + aprox err

    loop_f = out_f*ratio - out_f # 3.8 kHz

    # we sample the clocks at ps_f, since it's the fastest clock to control simulated logic
    actual_cmd = round(ideal_cmd)
    actual_phase = 0
    ideal_phase = 0
    time = 0
    shift_acc = 0
    fast_shift_cnt = 0 # one every seven seven shifts is a hard shift, other are smothed on 12 ticks @ ps_f
    shift_cooldown = 0
    loop_timer = 0

    phase_diff = ps_size_rad
    ps_cnt = 0
    for i in range(int(ps_f * sim_time)):
        if dither and loop_timer > 1/loop_f: # new softpll cycle
            #phase_diff_l.append(phase_diff)
            loop_timer -= 1/loop_f
            # assume the PI is perfect
            if phase_diff < 0: # i * (2**17-1) % 2 == 0: # phase_diff < 0: # too slow
                actual_cmd = np.ceil(ideal_cmd)
            else : # too fast
                actual_cmd = np.floor(ideal_cmd)

        time = i/ps_f
        loop_timer += 1/ps_f

        # MMCM internal logic
        phase_diff += out_f/ps_f *2*np.pi
        if shift_cooldown > 0: # shift
            if fast_shift_cnt > 7:
                fast_shift_cnt = 0
                shift_cooldown = 0
                phase_diff += ps_size_rad
            else :
                phase_diff += ps_size_rad/12
                shift_cooldown -= 1


        # MMCM PS ctrl logic
        shift_acc += actual_cmd
        if shift_acc > 2**(dac_bits + 3):
            shift_acc -= 2**(dac_bits + 3)
            shift_cooldown = 12
            fast_shift_cnt += 1

        phase_diff -= (ratio*out_f)/ps_f * 2 * np.pi
        if i % sample_div == 0:
            yield phase_diff

ps_f = 200e6
p = np.fromiter(sim(ps_f=ps_f), dtype='float16')
p = p - np.average(p)
f, psd = welch(p, ps_f, nperseg=2**22)
np.savez('welch_1G_noloop',f=f, psd=psd)
plt.plot(f, 10*np.log10(psd))
plt.xscale('log')
plt.figure()
plt.plot(np.linspace(-ps_f/2,ps_f/2, len(p)), np.abs(np.fft.fftshift(np.fft.fft(p))))
plt.show()
