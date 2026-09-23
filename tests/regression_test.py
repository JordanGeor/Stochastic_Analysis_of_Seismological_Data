from pathlib import Path

import numpy as np

from seismic_analysis.preprocessing import (
    load_waveform,
    load_inventory,
    preprocess_waveform,
)
from seismic_analysis.sta_lta import detect_phases_sta_lta
from seismic_analysis.stochastic import detect_stochastic_outbreak
from seismic_analysis.results import compare_detections


INVENTORY_PATH = "data/metadata/EVGI_station.xml"
WAVEFORM_DIRECTORY = "data/waveforms"


def main():
    inventory = load_inventory(INVENTORY_PATH)

    waveform_files = sorted(
        Path(WAVEFORM_DIRECTORY).glob("event_*.mseed")
    )

    delta_values = []

    print("\n--- 21 EVENT DETECTION TEST ---\n")

    for waveform_file in waveform_files:
        stream = load_waveform(str(waveform_file))

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

        delta_t = comparison["delta_t"]

        print(
            f"{waveform_file.name}: "
            f"STA={sta_result['p_seconds']} s | "
            f"SO={so_result['so_seconds']} s | "
            f"Delta t={delta_t}"
        )

        if delta_t is not None:
            delta_values.append(delta_t)

    print("\n--- SUMMARY ---")
    print(f"Total files: {len(waveform_files)}")
    print(f"Valid events: {len(delta_values)}")

    if not delta_values:
        print("No valid detection comparisons.")
        return

    delta_values = np.asarray(
        delta_values,
        dtype=float,
    )

    print(f"Mean:   {np.mean(delta_values):.4f} s")
    print(f"Std:    {np.std(delta_values):.4f} s")
    print(f"Median: {np.median(delta_values):.4f} s")
    print(f"Min:    {np.min(delta_values):.4f} s")
    print(f"Max:    {np.max(delta_values):.4f} s")


if __name__ == "__main__":
    main()