import os
import numpy as np
import matplotlib.pyplot as plt
from obspy import read
from scipy.signal import detrend
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit

# Συνάρτηση για να αφαιρέσεις την τάση από τα δεδομένα (κανονικοποίηση ή απομάκρυνση του μέσου όρου)
def preprocess_data(data):
    return detrend(data)  # Αφαιρούμε την τάση από τα δεδομένα

# Συνάρτηση υπολογισμού του συντελεστή συσχέτισης
def correlation_coefficient(x, y):
    x = preprocess_data(x)
    y = preprocess_data(y)

    if len(x) > 1 and len(np.unique(x)) > 1 and len(np.unique(y)) > 1:
        return np.corrcoef(x, y)[0, 1]
    else:
        return np.nan  # Επιστρέφουμε NaN αν τα δεδομένα δεν είναι αρκετά ή είναι όλα ίδια

# Συνάρτηση για Fourier Transform
def fourier_transform(data, sampling_rate):
    N = len(data)
    freqs = fftfreq(N, 1 / sampling_rate)
    fft_values = fft(data)
    return freqs[:N//2], np.abs(fft_values)[:N//2]  # Επιστρέφουμε μόνο τις θετικές συχνότητες

# Συνάρτηση fitting (παράδειγμα με γραμμική ή εκθετική προσαρμογή)
def fit_function(x, a, b):
    return a * np.exp(-b * x)  # Παράδειγμα εκθετικής προσαρμογής

def fit_data(x_data, y_data):
    # Κάνουμε fitting στα δεδομένα
    popt, _ = curve_fit(fit_function, x_data, y_data, p0=[1, 1])
    return popt

# Συνάρτηση για το σχέδιο του πρώτου κύματος με Fourier Transform
def plot_waveform_with_fourier(time_series, sampling_rate, outbreak_index):
    plt.figure(figsize=(10, 6))
    
    # Σχεδιάζουμε το σήμα
    plt.subplot(2, 1, 1)
    plt.plot(time_series, label="Waveform")
    plt.axvline(x=outbreak_index, color='r', linestyle='--', label="First Outbreak")
    plt.title("Waveform with First Outbreak")
    plt.xlabel("Time (samples)")
    plt.ylabel("Amplitude")
    plt.legend()

    # Υπολογισμός και σχεδίαση του Fourier Transform
    freqs, fft_values = fourier_transform(time_series, sampling_rate)
    plt.subplot(2, 1, 2)
    plt.plot(freqs, fft_values, label="FFT of the Signal", color='g')
    plt.title("Fourier Transform (Frequency Spectrum)")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude")
    plt.legend()

    plt.tight_layout()
    plt.show()

# Αναθεωρημένος αλγόριθμος SO για τη σύγκριση
def so_algorithm(time_series, sampling_rate, threshold):
    window_size = int(0.5 * sampling_rate)  
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
            print(f"OUTBREAK detected at sample {ct} (correlation drop)")
            plot_waveform_with_fourier(time_series, sampling_rate, ct)
            return ct

    print("No outbreak detected.")
    return None

# Φόρτωση αρχείων από το φάκελο 'cleaned_waveforms' και επεξεργασία τους
def process_files_from_folder(folder_path, sampling_rate, threshold):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mseed"):
            file_path = os.path.join(folder_path, filename)
            print(f"Επεξεργασία του αρχείου: {file_path}")
            
            try:
                st = read(file_path)
                trace = st[0]  # Πρώτο trace

                data = trace.data
                
                so_algorithm(data, sampling_rate, threshold)

            except Exception as e:
                print(f"Σφάλμα κατά τη φόρτωση ή επεξεργασία του αρχείου {file_path}: {e}")

# Παράδειγμα χρήσης
folder_path = r"C:\Users\user1\Desktop\EVGI\cleaned_waveforms"
sampling_rate = 100  # Συχνότητα δειγματοληψίας (Hz)
threshold = 0.5      # Κατώφλι συσχέτισης για εντοπισμό

process_files_from_folder(folder_path, sampling_rate, threshold)