import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from seismic_analysis.acquisition import (
    search_events,
    get_event_information,
)
from seismic_analysis.pipeline import analyze_events
from seismic_analysis.export import create_excel_file


st.set_page_config(
    page_title="Stochastic Seismic Analysis",
    page_icon="🌍",
    layout="wide",
)


st.title("Stochastic Analysis of Seismological Data")

st.write(
    "Search the NOA earthquake catalog and select seismic "
    "events for stochastic and signal analysis."
)

st.divider()


# --------------------------------------------------
# SEARCH PARAMETERS
# --------------------------------------------------

st.subheader("Earthquake Search")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start date",
    )

with col2:
    end_date = st.date_input(
        "End date",
    )


col1, col2, col3 = st.columns(3)

with col1:
    min_magnitude = st.number_input(
        "Minimum magnitude",
        min_value=0.0,
        max_value=10.0,
        value=3.5,
        step=0.1,
    )

with col2:
    latitude = st.number_input(
        "Center latitude",
        min_value=-90.0,
        max_value=90.0,
        value=38.62,
        step=0.01,
        format="%.4f",
    )

with col3:
    longitude = st.number_input(
        "Center longitude",
        min_value=-180.0,
        max_value=180.0,
        value=20.66,
        step=0.01,
        format="%.4f",
    )


radius_km = st.number_input(
    "Search radius (km)",
    min_value=1.0,
    value=100.0,
    step=10.0,
)


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

if st.button(
    "Search Earthquakes",
    type="primary",
    use_container_width=True,
):

    if end_date < start_date:
        st.error(
            "End date cannot be earlier than start date."
        )

    else:
        with st.spinner(
            "Searching NOA earthquake catalog..."
        ):

            try:
                events = search_events(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    min_magnitude=min_magnitude,
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=radius_km,
                )

                st.session_state["events"] = events

            except Exception as error:
                st.error(
                    f"Earthquake search failed: {error}"
                )


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "events" in st.session_state:

    events = st.session_state["events"]

    st.divider()

    st.subheader("Search Results")

    if not events:
        st.warning(
            "No earthquakes matched the search criteria."
        )

    else:
        st.success(
            f"{len(events)} earthquake(s) found."
        )

        rows = []

        for index, event in enumerate(
            events,
            start=1,
        ):
            info = get_event_information(event)

            rows.append(
                {
                    "Event": index,
                    "Date & Time": str(info["time"]),
                    "Magnitude": round(
                        info["magnitude"],
                        2,
                    ),
                    "Type": (
                        info["magnitude_type"] or ""
                    ),
                    "Latitude": round(
                        info["latitude"],
                        3,
                    ),
                    "Longitude": round(
                        info["longitude"],
                        3,
                    ),
                    "Depth (km)": (
                        round(info["depth_km"], 1)
                        if info["depth_km"]
                        is not None
                        else None
                    ),
                }
            )

        dataframe = pd.DataFrame(rows)

        # Add a checkbox column for event selection
        dataframe.insert(0, "Select", False)

        edited_dataframe = st.data_editor(
            dataframe,
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Event",
                "Date & Time",
                "Magnitude",
                "Type",
                "Latitude",
                "Longitude",
                "Depth (km)",
            ],
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select earthquakes for analysis.",
                    default=False,
                ),
            },
            key="event_selector",
        )

        selected_rows = edited_dataframe[
            edited_dataframe["Select"]
        ]

        selected_indices = (
            selected_rows["Event"]
            .astype(int)
            .tolist()
        )

        selected_events = [
            events[index - 1]
            for index in selected_indices
        ]

        st.write(
            f"**Selected earthquakes: "
            f"{len(selected_events)}**"
        )

        analyze_button = st.button(
            "Analyze Selected Events",
            type="primary",
            use_container_width=True,
            disabled=len(selected_events) == 0,
        )

        if analyze_button:
            st.session_state["selected_events"] = selected_events

            st.divider()
            st.subheader("Analysis")

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total, message):
                percentage = int(
                    (current - 1) / total * 100
                )

                progress_bar.progress(percentage)

                status_text.write(
                    f"{message} {current} of {total}..."
                )

            with st.spinner(
                "Downloading and analyzing seismic data..."
            ):
                results, errors = analyze_events(
                    selected_events,
                    progress_callback=update_progress,
                )

            progress_bar.progress(100)
            status_text.write("Analysis complete.")

            st.session_state["analysis_results"] = results
            st.session_state["analysis_errors"] = errors

            if results:
                st.success(
                    f"{len(results)} earthquake(s) "
                    "analyzed successfully."
                )

            if errors:
                st.warning(
                    f"{len(errors)} earthquake(s) "
                    "could not be analyzed."
                )

                for error in errors:
                    st.error(
                        f"Event {error['event_number']}: "
                        f"{error['error']}"
                    )

        # --------------------------------------------------
# ANALYSIS RESULTS
# --------------------------------------------------

if "analysis_results" in st.session_state:

    results = st.session_state["analysis_results"]

    if results:
        st.divider()
        st.subheader("Analysis Results")

        result_rows = []

        for result in results:
            event = result["event"]
            comparison = result["comparison"]
            signal = result["signal"]

            peak = signal["peak"]
            decay = signal["decay"]
            omega2 = signal["omega2"]

            omega2_scaled = result["signal"]["omega2_scaled"]

            result_rows.append(
                {
                    "Event": result["event_number"],
                    "Date & Time": str(event["time"]),
                    "Magnitude": round(
                        event["magnitude"],
                        2,
                    ),
                    "STA/LTA P (s)": (
                        round(
                            result["sta_lta"]["p_seconds"],
                            3,
                        )
                        if result["sta_lta"]["p_seconds"]
                        is not None
                        else None
                    ),
                    "STA/LTA S (s)": (
                        round(
                            result["sta_lta"]["s_seconds"],
                            3,
                        )
                        if result["sta_lta"]["s_seconds"]
                        is not None
                        else None
                    ),
                    "SO (s)": (
                        round(
                            result["stochastic"]["so_seconds"],
                            3,
                        )
                        if result["stochastic"]["so_seconds"]
                        is not None
                        else None
                    ),
                    "Δt (s)": (
                        round(
                            comparison["delta_t"],
                            3,
                        )
                        if comparison["delta_t"]
                        is not None
                        else None
                    ),
                    "Amax": peak["max_amplitude"],
                    "Decay a": decay["a"],
                    "Decay b": decay["b"],
                    "Decay c": decay["c"],
                    "Decay R²": decay["quality"]["r_squared"],
                    "Decay NRMSE": decay["quality"]["nrmse"],
                    "fc (Hz)": omega2_scaled["fc"],
                    "n": omega2_scaled["n"],
                    "γ": omega2_scaled["gamma"],
                    "ω² R²": omega2_scaled["quality"]["r_squared"],
                    "ω² NRMSE": omega2_scaled["quality"]["nrmse"],
                }
            )

        results_dataframe = pd.DataFrame(
            result_rows
        )

        st.dataframe(
            results_dataframe,
            use_container_width=True,
            hide_index=True,
        )

        # --------------------------------------------------
        # EXPORT RESULTS
        # --------------------------------------------------

        csv_data = results_dataframe.to_csv(
            index=False,
            sep=";",
        ).encode("utf-8-sig")

        excel_data = create_excel_file(
            results_dataframe
        )

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="seismic_analysis_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="seismic_analysis_results.xlsx",
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        # --------------------------------------------------
        # SUMMARY STATISTICS
        # --------------------------------------------------

        st.divider()
        st.subheader("Summary Statistics")

        delta_values = [
            result["comparison"]["delta_t"]
            for result in results
            if result["comparison"]["delta_t"]
            is not None
        ]

        if delta_values:
            delta_array = np.array(
                delta_values,
                dtype=float,
            )

            mean_delta = np.mean(delta_array)
            median_delta = np.median(delta_array)
            std_delta = np.std(delta_array)
            min_delta = np.min(delta_array)
            max_delta = np.max(delta_array)

            so_earlier = np.sum(
                delta_array < 0
            )

            sta_earlier = np.sum(
                delta_array > 0
            )

            same_time = np.sum(
                delta_array == 0
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Analyzed Events",
                    len(results),
                )

            with col2:
                st.metric(
                    "Mean Δt",
                    f"{mean_delta:.3f} s",
                )

            with col3:
                st.metric(
                    "Median Δt",
                    f"{median_delta:.3f} s",
                )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Standard Deviation",
                    f"{std_delta:.3f} s",
                )

            with col2:
                st.metric(
                    "Minimum Δt",
                    f"{min_delta:.3f} s",
                )

            with col3:
                st.metric(
                    "Maximum Δt",
                    f"{max_delta:.3f} s",
                )

            st.write(
                f"**SO detected earlier:** "
                f"{so_earlier} / {len(delta_array)}"
            )

            st.write(
                f"**STA/LTA detected earlier:** "
                f"{sta_earlier} / {len(delta_array)}"
            )

            if same_time > 0:
                st.write(
                    f"**Same detection time:** "
                    f"{same_time} / {len(delta_array)}"
                )

            fig, ax = plt.subplots(
                figsize=(10, 4)
            )

            event_numbers = list(
                range(
                    1,
                    len(delta_array) + 1,
                )
            )

            ax.bar(
                event_numbers,
                delta_array,
            )

            ax.axhline(
                0,
                linewidth=1.0,
            )

            ax.set_title(
                "STA/LTA vs SO Detection Time"
            )

            ax.set_xlabel(
                "Analyzed Event"
            )

            ax.set_ylabel(
                "Δt = tSO - tSTA/LTA (s)"
            )

            ax.set_xticks(
                event_numbers
            )

            ax.grid(
                True,
                axis="y",
                alpha=0.3,
            )

            fig.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

            st.caption(
                "Negative Δt: SO detected earlier. "
                "Positive Δt: STA/LTA detected earlier."
            )

        else:
            st.warning(
                "No valid Δt values are available "
                "for summary statistics."
            )

        # --------------------------------------------------
        # DETAILED ANALYSIS
        # --------------------------------------------------

        st.divider()
        st.subheader("Detailed Analysis")

        event_options = [
            f"Event {result['event_number']}"
            for result in results
        ]

        selected_event_name = st.selectbox(
            "Select earthquake",
            event_options,
        )

        selected_event_index = event_options.index(
            selected_event_name
        )

        selected_result = results[
            selected_event_index
        ]

        stream = selected_result["stream"]

        vertical_traces = stream.select(
            component="Z"
        )

        if len(vertical_traces) == 0:
            st.error(
                "No vertical Z component is available."
            )

        else:
            trace = vertical_traces[0]

            sta_result = selected_result["sta_lta"]
            so_result = selected_result["stochastic"]

            waveform_tab, so_tab, decay_tab, spectrum_tab = (
                st.tabs(
                    [
                        "Waveform & Picks",
                        "SO Correlation",
                        "Decay",
                        "Frequency Spectrum",
                    ]
                )
            )

            # ----------------------------------------------
            # WAVEFORM TAB
            # ----------------------------------------------

            with waveform_tab:
                times = trace.times()

                fig, ax = plt.subplots(
                    figsize=(12, 4)
                )

                ax.plot(
                    times,
                    trace.data,
                    linewidth=0.8,
                    label="Waveform",
                )

                if sta_result["p_seconds"] is not None:
                    ax.axvline(
                        sta_result["p_seconds"],
                        linestyle="--",
                        linewidth=2,
                        color="green",
                        label="STA/LTA P",
                    )

                if sta_result["s_seconds"] is not None:
                    ax.axvline(
                        sta_result["s_seconds"],
                        linestyle="--",
                        linewidth=2,
                        color="orange",
                        label="STA/LTA S",
                    )

                if so_result["so_seconds"] is not None:
                    ax.axvline(
                        so_result["so_seconds"],
                        linestyle="--",
                        linewidth=2,
                        color="red",
                        label="SO Detection",
                    )

                ax.set_title(
                    f"{selected_event_name} — EVGI HHZ"
                )

                ax.set_xlabel(
                    "Time from waveform start (s)"
                )

                ax.set_ylabel(
                    "Displacement (m)"
                )

                ax.grid(
                    True,
                    alpha=0.3,
                )

                ax.legend()

                fig.tight_layout()

                st.pyplot(fig)

                plt.close(fig)

            # ----------------------------------------------
            # SO CORRELATION TAB
            # ----------------------------------------------

            with so_tab:
                correlation_times = (
                    so_result["correlation_times"]
                )

                correlations = (
                    so_result["correlations"]
                )

                if len(correlations) == 0:
                    st.warning(
                        "No SO correlation data are available."
                    )

                else:
                    fig, ax = plt.subplots(
                        figsize=(12, 4)
                    )

                    ax.plot(
                        correlation_times,
                        correlations,
                        linewidth=1.0,
                        label="Correlation",
                    )

                    ax.axhline(
                        0.5,
                        linestyle="--",
                        label="SO Threshold (0.5)",
                    )

                    if (
                        so_result["so_seconds"]
                        is not None
                    ):
                        ax.axvline(
                            so_result["so_seconds"],
                            linestyle="--",
                            label="SO Detection",
                        )

                    ax.set_title(
                        f"{selected_event_name} "
                        "— Stochastic Outbreak"
                    )

                    ax.set_xlabel(
                        "Time from waveform start (s)"
                    )

                    ax.set_ylabel(
                        "Correlation coefficient"
                    )

                    ax.set_ylim(
                        -1.05,
                        1.05,
                    )

                    ax.grid(
                        True,
                        alpha=0.3,
                    )

                    ax.legend()

                    fig.tight_layout()

                    st.pyplot(fig)

                    plt.close(fig)

                    if (
                        so_result["so_seconds"]
                        is not None
                    ):
                        st.write(
                            "**SO detection:** "
                            f"{so_result['so_seconds']:.3f} s"
                        )

                    else:
                        st.info(
                            "No stochastic outbreak "
                            "was detected."
                        )

            # ----------------------------------------------
            # DECAY TAB
            # ----------------------------------------------

            with decay_tab:
                decay_result = (
                    selected_result["signal"]["decay"]
                )

                if not decay_result["success"]:
                    st.warning(
                        "The decay model could not be fitted "
                        "for this earthquake."
                    )

                else:
                    decay_time = decay_result["time"]
                    decay_data = decay_result["data"]
                    decay_fit = decay_result["fit"]

                    fig, ax = plt.subplots(
                        figsize=(12, 4)
                    )

                    ax.plot(
                        decay_time,
                        decay_data,
                        linewidth=1.0,
                        label="Observed decay",
                    )

                    ax.plot(
                        decay_time,
                        decay_fit,
                        linestyle="--",
                        linewidth=1.5,
                        label="Generalized exponential fit",
                    )

                    ax.set_title(
                        f"{selected_event_name} "
                        "— Amplitude Decay"
                    )

                    ax.set_xlabel(
                        "Time after maximum amplitude (s)"
                    )

                    ax.set_ylabel(
                        "Absolute displacement (m)"
                    )

                    ax.grid(
                        True,
                        alpha=0.3,
                    )

                    ax.legend()

                    fig.tight_layout()

                    st.pyplot(fig)

                    plt.close(fig)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "a",
                            f"{decay_result['a']:.3e}",
                        )

                    with col2:
                        st.metric(
                            "b",
                            f"{decay_result['b']:.4f}",
                        )

                    with col3:
                        st.metric(
                            "c",
                            f"{decay_result['c']:.4f}",
                        )

                        st.markdown("**Fit Quality**")

                        quality_col1, quality_col2 = st.columns(2)

                        decay_r2 = decay_result["quality"]["r_squared"]
                        decay_nrmse = decay_result["quality"]["nrmse"]

                        with quality_col1:
                            st.metric(
                                "R²",
                                f"{decay_r2:.4f}"
                                if decay_r2 is not None
                                else "N/A",
                            )

                        with quality_col2:
                            st.metric(
                                "NRMSE",
                                f"{decay_nrmse:.4f}"
                                if decay_nrmse is not None
                                else "N/A",
                            )

                    st.caption(
                        "Model: y(t) = a · exp(-(b · t)^c)"
                    )

            # ----------------------------------------------
            # FREQUENCY SPECTRUM TAB
            # ----------------------------------------------

            with spectrum_tab:
                fft_result = (
                    selected_result["signal"]["fft"]
                )

                omega2_result = (
                    selected_result["signal"]["omega2_scaled"]
                )

                frequencies = fft_result["frequencies"]
                amplitudes = fft_result["amplitude"]

                fig, ax = plt.subplots(
                    figsize=(12, 4)
                )

                ax.plot(
                    frequencies[1:],
                    amplitudes[1:],
                    linewidth=1.0,
                    label="FFT Spectrum",
                )

                if omega2_result["success"]:
                    ax.plot(
                        omega2_result["frequencies"],
                        omega2_result["fit"],
                        linestyle="--",
                        linewidth=1.5,
                        label="ω² Fit",
                    )

                ax.set_title(
                    f"{selected_event_name} "
                    "— Frequency Spectrum"
                )

                ax.set_xlabel(
                    "Frequency (Hz)"
                )

                ax.set_ylabel(
                    "Amplitude"
                )

                ax.set_xlim(
                    0,
                    20,
                )

                ax.grid(
                    True,
                    alpha=0.3,
                )

                ax.legend()

                fig.tight_layout()

                st.pyplot(fig)

                plt.close(fig)

                if omega2_result["success"]:

                    col1, col2, col3, col4 = (
                        st.columns(4)
                    )

                    with col1:
                        st.metric(
                            "A₀",
                            f"{omega2_result['A0']:.3e}",
                        )

                    with col2:
                        st.metric(
                            "fc",
                            f"{omega2_result['fc']:.3f} Hz",
                        )

                    with col3:
                        st.metric(
                            "n",
                            f"{omega2_result['n']:.3f}",
                        )

                    with col4:
                        st.metric(
                            "γ",
                            f"{omega2_result['gamma']:.3f}",
                        )

                    st.markdown("**Fit Quality**")

                    quality_col1, quality_col2 = st.columns(2)

                    omega2_r2 = (
                        omega2_result["quality"]["r_squared"]
                    )

                    omega2_nrmse = (
                        omega2_result["quality"]["nrmse"]
                    )

                    with quality_col1:
                        st.metric(
                            "R²",
                            f"{omega2_r2:.4f}"
                            if omega2_r2 is not None
                            else "N/A",
                        )

                    with quality_col2:
                        st.metric(
                            "NRMSE",
                            f"{omega2_nrmse:.4f}"
                            if omega2_nrmse is not None
                            else "N/A",
                        )

                else:
                    st.warning(
                        "The ω² model could not be fitted "
                        "for this earthquake."
                    )