# Stochastic Analysis of Seismological Data

Bachelor's thesis project developed at the **Department of Informatics, Ionian University**.

This project analyzes real seismic waveform data using stochastic, time-domain, and frequency-domain techniques. Its main objective is the detection and comparison of seismic P-wave arrivals using **STA/LTA** and the **Stochastic Outbreak (SO) Algorithm**.

## 🔍 Project Overview

The project implements a complete seismic data analysis workflow:

- Preprocessing of seismic waveforms
- Automatic P- and S-wave detection using STA/LTA
- P-wave detection using the Stochastic Outbreak Algorithm
- Comparison of the two detection methods
- Maximum amplitude and exponential decay analysis
- FFT and ω² spectral analysis

## 🌍 Dataset

The analysis uses real seismic recordings from the **National Observatory of Athens (NOA)**, focusing on the **EVGI seismic station**.

Waveforms are processed in MiniSEED (`.mseed`) format, primarily using the vertical component of the recordings.

## ⚙️ Methodology

Two phase-detection approaches are compared:

**STA/LTA (ObsPy)**  
Uses the ratio between short-term and long-term signal energy to detect seismic phase arrivals.

**Stochastic Outbreak (SO) Algorithm**  
Detects changes in the waveform by measuring the correlation between consecutive signal windows.

Additional analysis includes:

- Maximum waveform amplitude
- Generalized exponential decay fitting
- Fast Fourier Transform (FFT)
- ω² spectral model fitting

## 📊 Results

The comparison showed that the **SO-Algorithm generally detected the initial waveform change earlier than STA/LTA**.

STA/LTA provided more conventional phase detection and was also capable of identifying the S-wave.

Time-domain and spectral analyses were additionally used to characterize and evaluate the seismic recordings.

## 🛠 Technologies

- Python
- ObsPy
- NumPy
- SciPy
- Matplotlib

## 📂 Repository Structure

```text
EVGI/
├── data.py
├── disp.py
├── obspy_algorithm.py
├── SO-algorithm.py
└── catalague.py
```

The scripts cover seismic data preparation, phase detection, waveform analysis, decay fitting, and spectral analysis.

## ▶️ Usage

Clone the repository:

```bash
git clone https://github.com/JordanGeor/EVGI.git
cd EVGI
```

Install the required libraries:

```bash
pip install obspy numpy scipy matplotlib
```

Some scripts use local paths for the seismic waveform files. These paths must be adjusted before execution.

Example:

```bash
python obspy_algorithm.py
python SO-algorithm.py
python catalague.py
```

## 🎓 Academic Context

**Bachelor's Thesis:** *Stochastic Analysis of Seismological Data*  
**Original Title:** *Στοχαστική Ανάλυση σε Σεισμολογικά Δεδομένα*    
**University:** Ionian University  
**Department:** Department of Informatics  
**Supervisor:** Assistant Professor Iosif Polenakis  
**Year:** 2026


