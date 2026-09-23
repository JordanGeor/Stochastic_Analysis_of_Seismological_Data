import os
from obspy import read
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Γενικευμένη εκθετική αποσύνθεση
def gen_exponential(t, a, b, c):
    return a * np.exp(-(b * t) ** c)

# Μοντέλο φάσματος ω²
def omega2(f, A0, fc, n, gamma):
    fc = np.clip(fc, 1e-3, 1e3)
    exponent = (f / fc) ** (n * gamma)
    return A0 / (1 + exponent) ** (1.0 / gamma)

# FFT με επιλογή παραθύρου
def Transform(stream, npts, sampling_rate):
    fourier_data = 2 / stream.size * np.abs(np.fft.rfft(stream, n=npts))
    freqs = np.fft.rfftfreq(npts, 1 / sampling_rate)
    return fourier_data, freqs

# Φάκελος με cleaned waveforms
folder_path = r"C:\Users\user1\Desktop\EVGI\cleaned_waveforms"

for filename in os.listdir(folder_path):
    if filename.endswith(".mseed"):
        filepath = os.path.join(folder_path, filename)
        st = read(filepath)

        trZ = st.select(component="Z")
        if len(trZ) == 0:
            print(f"Δεν βρέθηκε Z component στο {filename}")
            continue
        tr = trZ[0]

        times = tr.times()
        df = tr.stats.sampling_rate

        # Μέγιστο πλάτος
        max_amp = np.max(np.abs(tr.data))
        max_index = np.abs(tr.data).argmax()
        max_time = tr.stats.starttime + (max_index / df)

        # Γενικευμένη εκθετική αποσύνθεση
        fit_seconds = 5
        fit_start = max_index
        fit_end = min(fit_start + int(fit_seconds * df), len(tr.data))

        x_fit = times[fit_start:fit_end] - times[fit_start]
        y_fit = np.abs(tr.data[fit_start:fit_end])
        mask = y_fit > 0
        x_fit_valid = x_fit[mask]
        y_fit_valid = y_fit[mask]

        try:
            if len(x_fit_valid) < 5:
                raise ValueError("Not enough points for exponential fit")

            popt_exp, _ = curve_fit(
                gen_exponential,
                x_fit_valid,
                y_fit_valid,
                p0=(max_amp, 1.0, 1.0),
                maxfev=100000
            )
            a_fit, b_fit, c_fit = popt_exp
            y_model = gen_exponential(x_fit_valid, *popt_exp)
            fit_label = f"y = {a_fit:.2f}·e^(-(({b_fit:.2f}·t)^{c_fit:.2f}))"
        except Exception as e:
            print(f"Exponential fit failed in {filename}: {e}")
            y_model = np.zeros_like(x_fit_valid)
            fit_label = "Fit failed"

        # Φάσμα με ω² μοντέλο
        pre = int(max(0, max_index - df * 5))
        post = int(min(len(tr.data), max_index + df * 5))
        segment = tr.data[pre:post]
        nfft = 2048

        ff, freqs = Transform(segment, nfft, df)

        try:
            p0 = (np.max(ff), 1.0, 2.0, 1.0)
            bounds = ([1e-10, 1e-2, 0.5, 0.5], [1e2, 50.0, 10.0, 5.0])
            popt, _ = curve_fit(
                omega2, freqs[1:], ff[1:],
                p0=p0, bounds=bounds, maxfev=100000
            )
            fc = abs(popt[1])
            fit_curve = omega2(freqs[1:], *popt)
            label = f"Fit: A0={popt[0]:.2e}, fc={fc:.2f} Hz, n={popt[2]:.2f}, γ={popt[3]:.2f}"
        except Exception as e:
            print(f"Spectrum fit failed in {filename}: {e}")
            fc = 0
            fit_curve = np.zeros_like(freqs[1:])
            label = "Fit failed"

        # Plot
        fig, axs = plt.subplots(
            3, 1, figsize=(12, 8), sharex=False,
            gridspec_kw={"height_ratios": [3, 2, 2]}
        )

        # 1. Κυματομορφή
        axs[0].plot(times, tr.data, 'k-', label="Waveform")
        axs[0].axvline(times[max_index], color='orange', linestyle='--', label='Max Amplitude')
        axs[0].set_title(f"{filename} - Max Amplitude: {max_amp:.4f}")
        axs[0].legend()
        axs[0].grid()

        # 2. Φάσμα με ω² fit
        axs[1].loglog(freqs[1:], ff[1:], 'r', label='FFT Spectrum')
        axs[1].loglog(freqs[1:], fit_curve, 'g--', label=label)
        axs[1].axvline(fc, color='black', linewidth=0.5, label=f'fc = {fc:.2f} Hz')
        axs[1].set_title("ω² Spectrum Fit")
        axs[1].set_xlabel("Frequency (Hz)")
        axs[1].set_ylabel("Amplitude")
        axs[1].legend()
        axs[1].grid(True, which='both', ls=':')

        # 3. Γενικευμένη Εκθετική Fit
        axs[2].plot(x_fit_valid, y_fit_valid, 'gray', label="Data (post-max)")
        axs[2].plot(x_fit_valid, y_model, 'b--', label=fit_label)
        axs[2].set_title("Generalized Exponential Decay Fit")
        axs[2].set_xlabel("Time after Max (s)")
        axs[2].set_ylabel("Amplitude")
        axs[2].legend()
        axs[2].grid()

        plt.tight_layout()
        plt.show()