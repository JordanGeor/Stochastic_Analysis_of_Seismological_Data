from pathlib import Path

from seismic_analysis.acquisition import (
    download_event_waveform,
    download_station_metadata,
    get_event_information,
)
from seismic_analysis.preprocessing import (
    load_inventory,
    preprocess_waveform,
)
from seismic_analysis.sta_lta import detect_phases_sta_lta
from seismic_analysis.stochastic import detect_stochastic_outbreak
from seismic_analysis.signal_analysis import analyze_signal
from seismic_analysis.results import compare_detections


DATA_DIR = Path("data")
WAVEFORM_DIR = DATA_DIR / "waveforms"
METADATA_DIR = DATA_DIR / "metadata"

STATION_XML = METADATA_DIR / "EVGI_station.xml"


def ensure_station_metadata():
    """
    Make sure EVGI station metadata are available.
    """

    if not STATION_XML.exists():
        download_station_metadata(STATION_XML)

    return load_inventory(STATION_XML)


def analyze_event(event, event_number, inventory):
    """
    Download and analyze one earthquake event.
    """

    WAVEFORM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    event_info = get_event_information(event)

    event_time = event_info["time"]

    timestamp = (
        f"{event_time.year:04d}"
        f"{event_time.month:02d}"
        f"{event_time.day:02d}_"
        f"{event_time.hour:02d}"
        f"{event_time.minute:02d}"
        f"{event_time.second:02d}"
    )

    waveform_path = (
        WAVEFORM_DIR
        / f"EVGI_{timestamp}.mseed"
    )

    stream = download_event_waveform(
        event=event,
        output_path=waveform_path,
    )

    cleaned_stream = preprocess_waveform(
        stream,
        inventory,
    )

    sta_result = detect_phases_sta_lta(
        cleaned_stream
    )

    so_result = detect_stochastic_outbreak(
        cleaned_stream
    )

    comparison = compare_detections(
        sta_result,
        so_result,
    )

    signal_result = analyze_signal(
        cleaned_stream
    )


    return {
        "event_number": event_number,
        "event": event_info,
        "waveform_path": waveform_path,
        "stream": cleaned_stream,
        "sta_lta": sta_result,
        "stochastic": so_result,
        "comparison": comparison,
        "signal": signal_result,
    }


def analyze_events(events, progress_callback=None):
    """
    Analyze multiple selected earthquakes.
    """

    inventory = ensure_station_metadata()

    results = []
    errors = []

    total_events = len(events)

    for index, event in enumerate(
        events,
        start=1,
    ):
        if progress_callback is not None:
            progress_callback(
                index,
                total_events,
                "Analyzing earthquake",
            )

        try:
            result = analyze_event(
                event=event,
                event_number=index,
                inventory=inventory,
            )

            results.append(result)

        except Exception as error:
            errors.append(
                {
                    "event_number": index,
                    "error": str(error),
                }
            )

    return results, errors