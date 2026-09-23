import numpy as np


# Parameters used in the original SO analysis
WINDOW_SIZE = 0.6
STEP_SIZE = 0.05
CORRELATION_THRESHOLD = 0.5


def correlation_coefficient(x, y):
    """
    Calculate the correlation coefficient exactly as in
    the original SO algorithm.
    """
    if (
        len(x) > 1
        and len(np.unique(x)) > 1
        and len(np.unique(y)) > 1
    ):
        return np.corrcoef(x, y)[0, 1]

    return np.nan


def detect_stochastic_outbreak(stream):
    """
    Detect the first stochastic outbreak using the same
    procedure as the original SO-algorithm.py.

    Consecutive 0.6-second windows are compared every
    0.05 seconds.

    An outbreak is detected when:

        0 < correlation < 0.5
    """

    vertical_traces = stream.select(component="Z")

    if len(vertical_traces) == 0:
        raise ValueError(
            "No vertical (Z) component found in the input stream."
        )

    tr = vertical_traces[0]

    data = tr.data
    sampling_rate = tr.stats.sampling_rate

    window_size = int(
        WINDOW_SIZE * sampling_rate
    )

    step = int(
        STEP_SIZE * sampling_rate
    )

    length = len(data)

    correlations = []
    correlation_times = []

    outbreak_sample = None

    for ct in range(
        window_size,
        length - window_size,
        step,
    ):
        old_window = data[
            ct - window_size:ct
        ]

        new_window = data[
            ct:ct + window_size
        ]

        correlation = correlation_coefficient(
            old_window,
            new_window,
        )

        correlations.append(correlation)
        correlation_times.append(
            ct / sampling_rate
        )

        # Exact legacy behaviour
        if (
            np.isnan(correlation)
            or correlation <= 0
        ):
            continue

        if correlation < CORRELATION_THRESHOLD:
            outbreak_sample = ct
            break

    if outbreak_sample is None:
        outbreak_seconds = None
        outbreak_time = None
    else:
        outbreak_seconds = (
            outbreak_sample / sampling_rate
        )

        outbreak_time = (
            tr.stats.starttime
            + outbreak_seconds
        )

    return {
        "so_time": outbreak_time,
        "so_sample": outbreak_sample,
        "so_seconds": outbreak_seconds,
        "correlations": np.asarray(
            correlations
        ),
        "correlation_times": np.asarray(
            correlation_times
        ),
        "sampling_rate": sampling_rate,
    }