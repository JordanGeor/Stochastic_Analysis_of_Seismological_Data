from obspy import read, read_inventory


def load_waveform(file_path):
    """
    Load a seismic waveform from a MiniSEED file.
    """
    return read(file_path)


def load_inventory(inventory_path):
    """
    Load station metadata from a StationXML file.
    """
    return read_inventory(inventory_path)


def preprocess_waveform(stream, inventory):
    """
    Preprocess a seismic waveform.

    Processing steps:
    - Attach instrument response
    - Linear detrend
    - Mean removal
    - 5% cosine taper
    - Band-pass filter from 1 to 20 Hz
    - Remove instrument response and convert to displacement
    """

    # Keep the original stream unchanged
    cleaned_stream = stream.copy()

    # Attach station response
    cleaned_stream.attach_response(inventory)

    # Detrend
    cleaned_stream.detrend("linear")
    cleaned_stream.detrend("demean")

    # Apply 5% cosine taper
    cleaned_stream.taper(
        max_percentage=0.05,
        type="cosine"
    )

    # Band-pass filter
    cleaned_stream.filter(
        "bandpass",
        freqmin=1,
        freqmax=20
    )

    # Instrument response removal
    pre_filt = [0.001, 1, 40, 45]

    cleaned_stream.remove_response(
        output="DISP",
        pre_filt=pre_filt
    )

    return cleaned_stream


def save_waveform(stream, output_path):
    """
    Save a processed waveform as MiniSEED.
    """
    stream.write(output_path, format="MSEED")