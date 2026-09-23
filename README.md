# Stochastic Analysis of Seismological Data

Bachelor's thesis project developed at the **Department of Informatics, Ionian University**.

This project analyzes real seismic waveform data using stochastic, time-domain, and frequency-domain techniques. Its main objective is the detection and comparison of seismic P-wave arrivals using **STA/LTA** and the **Stochastic Outbreak (SO) Algorithm**.

Following the completion and presentation of the bachelor's thesis, the original research code was further developed and refactored into a modular Python application.

The current repository therefore contains both the **original thesis implementation** and a **post-thesis software update** that introduces an interactive Streamlit interface, automated data acquisition, integrated analysis workflows, visualization, result export, and improved code organization.

## 🔍 Project Overview

The current version of the application provides a complete seismic-data analysis workflow:

- Search for earthquake events through the NOA FDSN service
- Select earthquake events through an interactive interface
- Automatically download seismic waveforms
- Preprocess waveform data
- Detect P- and S-wave arrivals using STA/LTA
- Detect initial waveform changes using the Stochastic Outbreak Algorithm
- Compare STA/LTA and SO detection times
- Detect maximum waveform amplitude
- Fit a generalized exponential decay model
- Perform Fast Fourier Transform (FFT) analysis
- Fit an ω² spectral model
- Evaluate model fits using R² and NRMSE
- Visualize analysis results
- Calculate summary statistics
- Export results to CSV and Excel

## 🌍 Seismic Data

The application uses real seismic data provided through the **National Observatory of Athens (NOA) FDSN service**.

The analysis is based on the vertical component of the **EVGI seismic station**:

```text
Network:  HT
Station:  EVGI
Location:
Channel:  HHZ
```

For each selected earthquake, a 60-second waveform window is retrieved:

- 10 seconds before the earthquake origin time
- 50 seconds after the earthquake origin time

Waveforms are stored locally in MiniSEED (`.mseed`) format.

## ⚙️ Preprocessing

Before detection and signal analysis, each waveform is processed using ObsPy.

The preprocessing sequence consists of:

1. Linear detrending
2. Mean removal
3. 5% cosine taper
4. Band-pass filtering between 1 and 20 Hz
5. Instrument-response removal
6. Conversion to displacement

Station-response information is obtained from the EVGI StationXML metadata.

## 📡 Detection Methods

### STA/LTA

The application uses ObsPy's recursive STA/LTA implementation.

Parameters:

```text
STA window:   0.1 s
LTA window:   2.0 s
Trigger on:   3.5
Trigger off:  1.0
```

The first detected trigger is interpreted as the P-wave arrival. When a second trigger is available, it is interpreted as the S-wave arrival.

### Stochastic Outbreak (SO) Algorithm

The Stochastic Outbreak method detects changes in the waveform by measuring the correlation between consecutive signal windows.

Parameters:

```text
Window size:            0.6 s
Step size:              0.05 s
Correlation threshold:  0.5
```

The two detection methods are compared using:

```text
Δt = tSO - tSTA/LTA
```

A negative Δt indicates that the SO method detected the initial waveform change before the STA/LTA P trigger.

## 📊 Signal Analysis

In addition to seismic detection, the application performs time-domain and frequency-domain signal analysis.

### Maximum Amplitude

The maximum absolute waveform amplitude and its corresponding time are automatically identified.

### Generalized Exponential Decay

A 5-second interval following the maximum amplitude is fitted using the generalized exponential model:

```text
y(t) = a · exp(-(b · t)^c)
```

The application reports:

- `a`
- `b`
- `c`
- R²
- NRMSE

### FFT and ω² Spectral Analysis

A Fast Fourier Transform is calculated around the maximum-amplitude region using an FFT size of 2048.

The resulting amplitude spectrum is fitted using an ω²-type spectral model.

Numerical amplitude scaling is applied during the optimization process to improve numerical conditioning. The fitted amplitude parameter is subsequently converted back to the original scale.

The spectral analysis reports:

- A₀
- Corner frequency (`fc`)
- Spectral exponent (`n`)
- Shape parameter (`γ`)
- R²
- NRMSE

## 🖥 Interactive Application

As part of the **post-thesis development**, the project now includes a Streamlit web interface.

The interface allows the user to:

1. Define earthquake-search parameters
2. Search the NOA earthquake catalog
3. Select one or more earthquakes
4. Run the complete analysis pipeline
5. Inspect waveform and phase-detection results
6. Examine SO correlation
7. Examine amplitude-decay fitting
8. Inspect the frequency spectrum and ω² fit
9. View summary statistics
10. Export results to CSV or Excel

## 🛠 Technologies

- Python
- ObsPy
- NumPy
- SciPy
- Pandas
- Matplotlib
- Streamlit
- OpenPyXL

## 📂 Repository Structure

```text
Stochastic_Analysis_of_Seismological_Data/
├── app.py
├── main.py
├── requirements.txt
│
├── seismic_analysis/
│   ├── __init__.py
│   ├── acquisition.py
│   ├── preprocessing.py
│   ├── sta_lta.py
│   ├── stochastic.py
│   ├── signal_analysis.py
│   ├── results.py
│   ├── export.py
│   └── pipeline.py
│
├── data/
│   ├── metadata/
│   │   └── EVGI_station.xml
│   └── waveforms/
│
├── tests/
│   ├── __init__.py
│   └── regression_test.py
│
└── legacy/
    ├── catalague.py
    ├── data.py
    ├── disp.py
    ├── obspy_algorithm.py
    └── SO-algorithm.py
```

The `legacy/` directory preserves the original standalone scripts developed during the thesis.

The current application uses the modular implementation contained in `seismic_analysis/`.

## ▶️ Installation

Clone the repository:

```bash
git clone https://github.com/JordanGeor/Stochastic_Analysis_of_Seismological_Data.git
cd Stochastic_Analysis_of_Seismological_Data
```

Install the required dependencies:

```bash
python -m pip install -r requirements.txt
```

## ▶️ Running the Application

Start the Streamlit application with:

```bash
python -m streamlit run app.py
```

Streamlit will start a local web server, typically available at:

```text
http://localhost:8501
```

The earthquake search, event selection, analysis, visualization, and export workflow can then be performed directly through the browser.

## 🔄 Post-Thesis Development

The original version of this project was developed and used as part of the bachelor's thesis presented in 2026.

The thesis implementation consisted primarily of separate Python scripts for:

- earthquake catalog retrieval
- waveform preprocessing
- STA/LTA phase detection
- Stochastic Outbreak detection
- maximum-amplitude and decay analysis
- FFT and ω² spectral analysis

After the completion and presentation of the thesis, the project was further developed as a software-engineering and portfolio project.

The post-thesis update introduces:

- a modular Python architecture
- an integrated analysis pipeline
- automated NOA FDSN data retrieval
- interactive earthquake search and selection
- a Streamlit web interface
- integrated analysis visualizations
- fit-quality metrics
- summary statistics
- CSV and Excel export
- regression testing
- improved project organization and maintainability

The original thesis scripts are preserved in the `legacy/` directory so that the earlier implementation remains available for reference.

The post-thesis version represents a subsequent software development of the original research project and should not be interpreted as the exact software version used during the original thesis presentation.

## 📝 Reproducibility Note

Earthquake catalogs and waveform data are retrieved from an external FDSN service. The data currently returned by the service may change over time.

Consequently, running the current application at a later date may not reproduce every historical intermediate value or aggregate statistic obtained during the original thesis analysis.

The original standalone implementations are preserved in `legacy/` as a reference to the project's original development.

## 🎓 Academic Context

**Bachelor's Thesis:** *Stochastic Analysis of Seismological Data*  
**Original Title:** *Στοχαστική Ανάλυση σε Σεισμολογικά Δεδομένα*
**University:** Ionian University  
**Department:** Department of Informatics  
**Supervisor:** Assistant Professor Iosif Polenakis  
**Year:** 2026

The bachelor's thesis was completed and presented before the post-thesis software refactoring contained in the current version of this repository.
