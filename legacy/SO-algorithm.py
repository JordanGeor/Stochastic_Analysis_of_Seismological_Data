import os
import numpy as np
import matplotlib.pyplot as plt
from obspy import read
from scipy.optimize import curve_fit

# Συνάρτηση υπολογισμού του συντελεστή συσχέτισης
def correlation_coefficient(x, y):
    if len(x) > 1 and len(np.unique(x)) > 1 and len(np.unique(y)) > 1:
        return np.corrcoef(x, y)[0, 1]
    else:
        return np.nan

# Συνάρτηση fitting
def fit_function(x, a, b):
    return a * np.exp(-b * x)

def fit_data(x_data, y_data):
    popt, _ = curve_fit(fit_function, x_data, y_data, p0=[1, 1])
    return popt

# Σχεδίαση ΜΟΝΟ του waveform (ΧΩΡΙΣ Fourier Transform)
def plot_waveform(time_series, outbreak_index, sampling_rate, filename):
    plt.figure(figsize=(10, 4))

    t = outbreak_index / sampling_rate

    plt.plot(time_series, label="Waveform")
    plt.axvline(
        x=outbreak_index,
        color='r',
        linestyle='--',
        label=f"First Outbreak (t = {t:.2f} s)"
    )

    plt.title(f"Waveform: {filename}")
    plt.xlabel("Time (samples)")
    plt.ylabel("Amplitude")
    plt.legend()

    plt.tight_layout()
    plt.show()

def so_algorithm(time_series, sampling_rate, threshold, filename):
    window_size = int(0.6 * sampling_rate)
    step = int(0.05 * sampling_rate)

    L = len(time_series)

    for ct in range(window_size, L - window_size, step):
        old_window = time_series[ct - window_size:ct]
        new_window = time_series[ct:ct + window_size]

        r_ct = correlation_coefficient(old_window, new_window)
        print(f"r({ct}) = {r_ct}")

        if np.isnan(r_ct) or r_ct <= 0:
            continue

        if r_ct < threshold:
            t = ct / sampling_rate
            print(f"OUTBREAK detected in file {filename} at sample {ct} (correlation drop)")
            print(f"Time of outbreak: t = {t:.2f} seconds")
            plot_waveform(time_series, ct, sampling_rate, filename)
            return ct

    print(f"No outbreak detected in file {filename}.")
    return None

# Φόρτωση αρχείων από το φάκελο 'cleaned_waveforms' και επεξεργασία τους
def process_files_from_folder(folder_path, sampling_rate, threshold):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mseed"):
            file_path = os.path.join(folder_path, filename)
            print(f"\nΕπεξεργασία του αρχείου: {file_path}")

            try:
                st = read(file_path)
                trace = st[0]

                data = trace.data

                outbreak_sample = so_algorithm(data, sampling_rate, threshold, filename)

                if outbreak_sample is not None:
                    outbreak_time = outbreak_sample / sampling_rate
                    print(f"Τελικό αποτέλεσμα για το αρχείο {filename}:")
                    print(f"Outbreak sample = {outbreak_sample}")
                    print(f"Outbreak time t = {outbreak_time:.2f} s")
                else:
                    print(f"Δεν βρέθηκε outbreak στο αρχείο {filename}")

            except Exception as e:
                print(f"Σφάλμα κατά τη φόρτωση ή επεξεργασία του αρχείου {file_path}: {e}")

# Παράδειγμα χρήσης
folder_path = r"C:\Users\user1\Desktop\EVGI\cleaned_waveforms"
sampling_rate = 100
threshold = 0.5

process_files_from_folder(folder_path, sampling_rate, threshold)