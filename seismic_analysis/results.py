def compare_detections(sta_result, so_result):
    """
    Compare the P-wave detection from STA/LTA with the
    detection from the Stochastic Outbreak algorithm.

    Delta t is defined as:

        Δt = t_SO - t_STA/LTA

    Therefore:
        Δt < 0  -> SO detected earlier
        Δt > 0  -> STA/LTA detected earlier
        Δt = 0  -> both detected at the same time

    Parameters
    ----------
    sta_result : dict
        Result returned by detect_phases_sta_lta().

    so_result : dict
        Result returned by detect_stochastic_outbreak().

    Returns
    -------
    dict
        Detection times and their difference in seconds.
    """

    sta_p_time = sta_result.get("p_time")
    so_time = so_result.get("so_time")

    # Comparison is not possible if either method
    # failed to produce a detection.
    if sta_p_time is None or so_time is None:
        delta_t = None
    else:
        delta_t = float(so_time - sta_p_time)

    return {
        "sta_lta_p_time": sta_p_time,
        "sta_lta_s_time": sta_result.get("s_time"),
        "so_time": so_time,
        "delta_t": delta_t,
    }