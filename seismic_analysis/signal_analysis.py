import numpy as np
from scipy.optimize import curve_fit


# Analysis parameters used in the original analysis
DECAY_DURATION = 5.0
FFT_WINDOW = 5.0
NFFT = 2048


def generalized_exponential(t, a, b, c):
    """
    Generalized exponential decay model used in the
    original analysis.

    y(t) = a * exp(-(b*t)^c)
    """
    return a * np.exp(-((b * t) ** c))


def omega2_model(frequency, A0, fc, n, gamma):
    """
    Generalized omega-square spectral model used in
    the original analysis.
    """
    fc = np.clip(fc, 1e-3, 1e3)

    exponent = (
        frequency / fc
    ) ** (n * gamma)

    return A0 / (
        1 + exponent
    ) ** (1.0 / gamma)

def calculate_fit_quality(observed, fitted):
    observed = np.asarray(observed, dtype=float)
    fitted = np.asarray(fitted, dtype=float)

    if observed.size == 0 or fitted.size == 0:
        return {
            "r_squared": None,
            "nrmse": None,
        }

    if observed.size != fitted.size:
        return {
            "r_squared": None,
            "nrmse": None,
        }

    residuals = observed - fitted

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum(
        (observed - np.mean(observed)) ** 2
    )

    if ss_tot == 0:
        r_squared = None
    else:
        r_squared = 1 - (ss_res / ss_tot)

    rmse = np.sqrt(np.mean(residuals ** 2))

    data_range = np.max(observed) - np.min(observed)

    if data_range == 0:
        nrmse = None
    else:
        nrmse = rmse / data_range

    return {
        "r_squared": (
            None
            if r_squared is None
            else float(r_squared)
        ),
        "nrmse": (
            None
            if nrmse is None
            else float(nrmse)
        ),
    }

def get_vertical_trace(stream):
    """
    Return the vertical Z component.
    """
    vertical_traces = stream.select(
        component="Z"
    )

    if len(vertical_traces) == 0:
        raise ValueError(
            "No vertical (Z) component found."
        )

    return vertical_traces[0]


def find_max_amplitude(stream):
    """
    Find maximum absolute amplitude and its time.
    """
    tr = get_vertical_trace(stream)

    sampling_rate = tr.stats.sampling_rate

    max_amplitude = float(
        np.max(np.abs(tr.data))
    )

    peak_sample = int(
        np.abs(tr.data).argmax()
    )

    peak_seconds = (
        peak_sample / sampling_rate
    )

    peak_time = (
        tr.stats.starttime + peak_seconds
    )

    return {
        "max_amplitude": max_amplitude,
        "peak_sample": peak_sample,
        "peak_seconds": peak_seconds,
        "peak_time": peak_time,
    }


def fit_decay(stream, peak_sample=None):
    """
    Fit the generalized exponential decay model
    for 5 seconds following the maximum amplitude.

    This reproduces the fitting procedure used in
    the original catalague.py analysis.
    """
    tr = get_vertical_trace(stream)

    sampling_rate = tr.stats.sampling_rate
    times = tr.times()

    if peak_sample is None:
        peak_result = find_max_amplitude(
            stream
        )
        peak_sample = peak_result[
            "peak_sample"
        ]

    fit_end = min(
        peak_sample
        + int(
            DECAY_DURATION
            * sampling_rate
        ),
        len(tr.data),
    )

    x_fit = (
        times[peak_sample:fit_end]
        - times[peak_sample]
    )

    y_fit = np.abs(
        tr.data[peak_sample:fit_end]
    )

    # Same mask used in the legacy analysis
    mask = y_fit > 0

    x_fit_valid = x_fit[mask]
    y_fit_valid = y_fit[mask]

    if len(x_fit_valid) < 5:
        return {
            "a": None,
            "b": None,
            "c": None,
            "time": x_fit_valid,
            "data": y_fit_valid,
            "fit": None,
            "covariance": None,
            "success": False,
        }

    max_amplitude = float(
        np.max(np.abs(tr.data))
    )

    try:
        parameters, covariance = curve_fit(
            generalized_exponential,
            x_fit_valid,
            y_fit_valid,
            p0=(
                max_amplitude,
                1.0,
                1.0,
            ),
            maxfev=100000,
        )

        a, b, c = parameters

        fitted_decay = (
            generalized_exponential(
                x_fit_valid,
                *parameters,
            )
        )

        success = True

    except Exception:
        a = None
        b = None
        c = None
        covariance = None
        fitted_decay = None
        success = False

    return {
        "a": (
            None if a is None
            else float(a)
        ),
        "b": (
            None if b is None
            else float(b)
        ),
        "c": (
            None if c is None
            else float(c)
        ),
        "time": x_fit_valid,
        "data": y_fit_valid,
        "fit": fitted_decay,
        "covariance": covariance,
        "success": success,
    }


def calculate_fft(
    stream,
    peak_sample=None,
):
    """
    Calculate the FFT using the same ±5 second
    window and normalization as catalague.py.
    """
    tr = get_vertical_trace(stream)

    sampling_rate = tr.stats.sampling_rate

    if peak_sample is None:
        peak_result = find_max_amplitude(
            stream
        )
        peak_sample = peak_result[
            "peak_sample"
        ]

    pre = int(
        max(
            0,
            peak_sample
            - sampling_rate * FFT_WINDOW,
        )
    )

    post = int(
        min(
            len(tr.data),
            peak_sample
            + sampling_rate * FFT_WINDOW,
        )
    )

    segment = tr.data[pre:post]

    if segment.size == 0:
        raise ValueError(
            "No samples available for FFT."
        )

    # Exact normalization used by the
    # original Transform() function
    amplitude_spectrum = (
        2
        / segment.size
        * np.abs(
            np.fft.rfft(
                segment,
                n=NFFT,
            )
        )
    )

    frequencies = np.fft.rfftfreq(
        NFFT,
        1 / sampling_rate,
    )

    return {
        "frequencies": frequencies,
        "amplitude": amplitude_spectrum,
        "start_sample": pre,
        "end_sample": post,
    }


def fit_omega2(frequencies, amplitude_spectrum):
    frequencies = np.asarray(frequencies)
    amplitude_spectrum = np.asarray(amplitude_spectrum)

    f = frequencies[1:]
    amplitude = amplitude_spectrum[1:]

    initial_guess = (
        np.max(amplitude_spectrum),
        1.0,
        2.0,
        1.0,
    )

    bounds = (
        [1e-10, 1e-2, 0.5, 0.5],
        [1e2, 50.0, 10.0, 5.0],
    )

    debug_info = {
        "frequency_min": float(np.min(f)),
        "frequency_max": float(np.max(f)),
        "amplitude_min": float(np.min(amplitude)),
        "amplitude_max": float(np.max(amplitude)),
        "initial_A0": float(initial_guess[0]),
        "initial_fc": float(initial_guess[1]),
        "initial_n": float(initial_guess[2]),
        "initial_gamma": float(initial_guess[3]),
    }

    try:
        parameters, covariance = curve_fit(
            omega2_model,
            f,
            amplitude,
            p0=initial_guess,
            bounds=bounds,
            maxfev=100000,
        )

        A0, fc, n, gamma = parameters
        fc = abs(fc)

        fitted_spectrum = omega2_model(
            f,
            *parameters,
        )

        success = True

    except Exception as error:
        A0 = fc = n = gamma = None
        covariance = None
        fitted_spectrum = None
        success = False

        debug_info["error"] = str(error)

    return {
        "A0": None if A0 is None else float(A0),
        "fc": None if fc is None else float(fc),
        "n": None if n is None else float(n),
        "gamma": None if gamma is None else float(gamma),
        "frequencies": f,
        "fit": fitted_spectrum,
        "covariance": covariance,
        "success": success,
        "debug": debug_info,
    }

def fit_omega2_scaled(frequencies, amplitude_spectrum):
    frequencies = np.asarray(frequencies, dtype=float)
    amplitude_spectrum = np.asarray(amplitude_spectrum, dtype=float)

    f = frequencies[1:]
    amplitude = amplitude_spectrum[1:]

    if amplitude.size == 0:
        return {
            "A0": None,
            "fc": None,
            "n": None,
            "gamma": None,
            "frequencies": f,
            "fit": None,
            "success": False,
            "scale_factor": None,
        }

    scale_factor = float(np.max(amplitude))

    if scale_factor <= 0:
        return {
            "A0": None,
            "fc": None,
            "n": None,
            "gamma": None,
            "frequencies": f,
            "fit": None,
            "success": False,
            "scale_factor": scale_factor,
        }

    # Normalize amplitudes so that their numerical scale is close to 1.
    amplitude_scaled = amplitude / scale_factor

    initial_guess = (
        1.0,   # scaled A0
        1.0,   # fc
        2.0,   # n
        1.0,   # gamma
    )

    bounds = (
        [1e-6, 1e-2, 0.5, 0.5],
        [100.0, 50.0, 10.0, 5.0],
    )

    try:
        parameters, covariance = curve_fit(
            omega2_model,
            f,
            amplitude_scaled,
            p0=initial_guess,
            bounds=bounds,
            maxfev=100000,
        )

        A0_scaled, fc, n, gamma = parameters

        # Convert A0 back to the original amplitude scale.
        A0 = A0_scaled * scale_factor

        fitted_scaled = omega2_model(
            f,
            *parameters,
        )

        fitted_spectrum = fitted_scaled * scale_factor

        success = True

    except Exception:
        A0 = fc = n = gamma = None
        covariance = None
        fitted_spectrum = None
        success = False

    return {
        "A0": None if A0 is None else float(A0),
        "fc": None if fc is None else float(fc),
        "n": None if n is None else float(n),
        "gamma": None if gamma is None else float(gamma),
        "frequencies": f,
        "fit": fitted_spectrum,
        "covariance": covariance,
        "success": success,
        "scale_factor": scale_factor,
    }

def analyze_signal(stream):
    peak_result = find_max_amplitude(stream)
    peak_sample = peak_result["peak_sample"]

    decay_result = fit_decay(
        stream,
        peak_sample=peak_sample,
    )

    fft_result = calculate_fft(
        stream,
        peak_sample=peak_sample,
    )

    # Original / legacy omega² fit
    omega2_result = fit_omega2(
        fft_result["frequencies"],
        fft_result["amplitude"],
    )

    # Experimental scaled omega² fit
    omega2_scaled_result = fit_omega2_scaled(
        fft_result["frequencies"],
        fft_result["amplitude"],
    )


    # Decay fit quality
    if decay_result["success"]:
        decay_quality = calculate_fit_quality(
            decay_result["data"],
            decay_result["fit"],
        )
    else:
        decay_quality = {
            "r_squared": None,
            "nrmse": None,
        }

    # Original omega² fit quality
    if omega2_result["success"]:
        observed_spectrum = fft_result["amplitude"][1:]

        omega2_quality = calculate_fit_quality(
            observed_spectrum,
            omega2_result["fit"],
        )
    else:
        omega2_quality = {
            "r_squared": None,
            "nrmse": None,
        }

    # Scaled omega² fit quality
    if omega2_scaled_result["success"]:
        observed_spectrum = fft_result["amplitude"][1:]

        omega2_scaled_quality = calculate_fit_quality(
            observed_spectrum,
            omega2_scaled_result["fit"],
        )
    else:
        omega2_scaled_quality = {
            "r_squared": None,
            "nrmse": None,
        }


    decay_result["quality"] = decay_quality
    omega2_result["quality"] = omega2_quality
    omega2_scaled_result["quality"] = omega2_scaled_quality
    return {
        "peak": peak_result,
        "decay": decay_result,
        "fft": fft_result,
        "omega2": omega2_result,
        "omega2_scaled": omega2_scaled_result,
    }

    # --------------------------------------------------
    # FIT QUALITY DIAGNOSTICS
    # --------------------------------------------------

    if decay_result["success"]:
        decay_quality = calculate_fit_quality(
            decay_result["data"],
            decay_result["fit"],
        )
    else:
        decay_quality = {
            "r_squared": None,
            "nrmse": None,
        }

    if omega2_result["success"]:
        observed_spectrum = fft_result["amplitude"][1:]

        omega2_quality = calculate_fit_quality(
            observed_spectrum,
            omega2_result["fit"],
        )
    else:
        omega2_quality = {
            "r_squared": None,
            "nrmse": None,
        }

    decay_result["quality"] = decay_quality
    omega2_result["quality"] = omega2_quality

    return {
        "peak": peak_result,
        "decay": decay_result,
        "fft": fft_result,
        "omega2": omega2_result,
    }