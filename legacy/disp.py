import os
from obspy import read, read_inventory

# Διαδρομή στον φάκελο EVGI στην επιφάνεια εργασίας
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
evgi_folder = os.path.join(desktop_path, "EVGI")
waveforms_folder = os.path.join(evgi_folder, "waveforms")
cleaned_folder = os.path.join(evgi_folder, "cleaned_waveforms")

# Δημιουργία φακέλου για τα καθαρισμένα αρχεία
if not os.path.exists(cleaned_folder):
    os.makedirs(cleaned_folder)

# Ανάγνωση του inventory
inventory_file = os.path.join(evgi_folder, "EVGI_station.xml")
inventory = read_inventory(inventory_file)

# Λήψη όλων των αρχείων miniSEED
mseed_files = [f for f in os.listdir(waveforms_folder) if f.endswith(".mseed")]

# Καθαρισμός και εμφάνιση κάθε waveform
for mseed_file in mseed_files:
    try:
        # Διαδρομή στο αρχείο
        mseed_path = os.path.join(waveforms_folder, mseed_file)

        # Ανάγνωση αρχείου miniSEED
        st = read(mseed_path)
        print(f"Διαβάστηκε το αρχείο: {mseed_file}")

        # Επισύναψη της απόκρισης του σταθμού
        st.attach_response(inventory)

        # Καθαρισμός των δεδομένων
        st.detrend('linear')
        st.detrend('demean')
        st.taper(max_percentage=0.05, type='cosine')
        st.filter("bandpass", freqmin=1, freqmax=20)
        pre_filt = [0.001, 1, 40, 45]
        st.remove_response(output="DISP", pre_filt=pre_filt)

        # Εμφάνιση της καθαρισμένης κυματομορφής
        print(f"Εμφάνιση καθαρισμένης κυματομορφής για το αρχείο: {mseed_file}")
        st.plot() 

        # Αποθήκευση του καθαρισμένου waveform
        cleaned_path = os.path.join(cleaned_folder, f"cleaned_{mseed_file}")
        st.write(cleaned_path, format="MSEED")
        print(f"Αποθηκεύτηκε το καθαρισμένο αρχείο: {cleaned_path}")

    except Exception as e:
        print(f"Σφάλμα κατά την επεξεργασία του αρχείου {mseed_file}: {str(e)}")
