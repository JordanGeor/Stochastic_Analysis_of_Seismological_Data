import os
from obspy import read
from obspy.signal.trigger import recursive_sta_lta, trigger_onset
import matplotlib.pyplot as plt

# Φάκελος με Καθαρισμένα σεισμικά δεδομένα
folder_path = r"C:\Users\user1\Desktop\EVGI\cleaned_waveforms"

# Παράμετροι STA/LTA
sta = 0.1
lta = 2.0
trigger_on = 3.5
trigger_off = 1.0

# Χρονικά περιθώρια
pre_buffer = 2.0
post_buffer = 8.0

for filename in os.listdir(folder_path):
    if not filename.endswith(".mseed"):
        continue

    filepath = os.path.join(folder_path, filename)
    st = read(filepath)

    # Z component 
    tr = st.select(component="Z")[0]


    df = tr.stats.sampling_rate
    nsta = int(sta * df)
    nlta = int(lta * df)

    cft = recursive_sta_lta(tr.data, nsta, nlta)
    onsets = trigger_onset(cft, trigger_on, trigger_off)

    # Χρόνοι
    p_time = s_time = None
    p_sample = s_sample = None
    p_sec = s_sec = None

    # Ορισμός P και S ως 1ο και 2ο trigger
    if len(onsets) >= 1:
        p_sample = onsets[0][0]
        p_time = tr.stats.starttime + p_sample / df
        p_sec = p_sample / df

    if len(onsets) >= 2:
        s_sample = onsets[1][0]
        s_time = tr.stats.starttime + s_sample / df
        s_sec = s_sample / df

    # Υπολογισμός ορίων προβολής
    start_plot = tr.stats.starttime
    end_plot = tr.stats.endtime

    if p_time:
        start_plot = max(tr.stats.starttime, p_time - pre_buffer)
    if s_time:
        end_plot = min(tr.stats.endtime, s_time + post_buffer)

    # Πλοκή waveform με γραμμές P και S
    fig, ax = plt.subplots()
    t = tr.times("matplotlib")
    ax.plot_date(t, tr.data, "k-", label=tr.id)

    ymin, ymax = ax.get_ylim()
    y_text = ymin + 0.08 * (ymax - ymin)

    if p_time:
        ax.axvline(
            p_time.matplotlib_date,
            color="blue",
            label=f"P-wave (t = {p_sec:.3f} s)",
        )
        ax.text(
            p_time.matplotlib_date,
            y_text,
            f"{p_sec:.3f} s",
            color="blue",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=9,
        )

    if s_time:
        ax.axvline(
            s_time.matplotlib_date,
            color="red",
            label=f"S-wave (t = {s_sec:.3f} s)",
        )
        ax.text(
            s_time.matplotlib_date,
            y_text,
            f"{s_sec:.3f} s",
            color="red",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=9,
        )

    ax.set_xlim([start_plot.matplotlib_date, end_plot.matplotlib_date])
    ax.legend()
    ax.set_title(f"Waveform: {filename}")
    fig.autofmt_xdate()
    plt.show()