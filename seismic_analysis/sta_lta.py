from obspy.signal.trigger import recursive_sta_lta, trigger_onset


# STA/LTA parameters used in the original analysis
STA_WINDOW = 0.1
LTA_WINDOW = 2.0
TRIGGER_ON = 3.5
TRIGGER_OFF = 1.0


def detect_phases_sta_lta(stream):
    """
    Detect P- and S-wave arrivals using recursive STA/LTA.

    The first trigger is interpreted as the P-wave arrival
    and the second trigger as the S-wave arrival.

    Parameters
    ----------
    stream : obspy.Stream
        Preprocessed seismic waveform.

    Returns
    -------
    dict
        STA/LTA detection results containing P and S arrival
        times, sample positions, relative times and the
        characteristic function.
    """

    # Select the vertical component, as in the original analysis
    vertical_traces = stream.select(component="Z")

    if len(vertical_traces) == 0:
        raise ValueError(
            "No vertical (Z) component found in the input stream."
        )

    tr = vertical_traces[0]

    sampling_rate = tr.stats.sampling_rate

    # Convert STA/LTA windows from seconds to samples
    nsta = int(STA_WINDOW * sampling_rate)
    nlta = int(LTA_WINDOW * sampling_rate)

    # Calculate recursive STA/LTA characteristic function
    cft = recursive_sta_lta(
        tr.data,
        nsta,
        nlta
    )

    # Detect trigger intervals
    onsets = trigger_onset(
        cft,
        TRIGGER_ON,
        TRIGGER_OFF
    )

    # Default values when phases are not detected
    p_sample = None
    s_sample = None

    p_time = None
    s_time = None

    p_seconds = None
    s_seconds = None

    # First trigger = P-wave
    if len(onsets) >= 1:
        p_sample = int(onsets[0][0])
        p_seconds = p_sample / sampling_rate
        p_time = tr.stats.starttime + p_seconds

    # Second trigger = S-wave
    if len(onsets) >= 2:
        s_sample = int(onsets[1][0])
        s_seconds = s_sample / sampling_rate
        s_time = tr.stats.starttime + s_seconds

    return {
        "p_time": p_time,
        "s_time": s_time,
        "p_sample": p_sample,
        "s_sample": s_sample,
        "p_seconds": p_seconds,
        "s_seconds": s_seconds,
        "characteristic_function": cft,
        "triggers": onsets,
        "sampling_rate": sampling_rate,
    }