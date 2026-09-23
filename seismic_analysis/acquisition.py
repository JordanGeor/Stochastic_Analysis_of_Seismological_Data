from pathlib import Path

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException


FDSN_CLIENT = "NOA"

DEFAULT_NETWORK = "HT"
DEFAULT_STATION = "EVGI"
DEFAULT_LOCATION = ""
DEFAULT_CHANNEL = "HHZ"

PRE_EVENT_SECONDS = 10
POST_EVENT_SECONDS = 50

KM_PER_DEGREE = 111.19


def km_to_degrees(radius_km):
    """
    Convert an approximate search radius from kilometres
    to angular degrees for the FDSN event query.
    """
    if radius_km <= 0:
        raise ValueError("Search radius must be greater than 0 km.")

    return radius_km / KM_PER_DEGREE


def search_events(
    start_date,
    end_date,
    min_magnitude,
    latitude,
    longitude,
    radius_km,
    max_events=None,
):
    """
    Search the NOA earthquake catalog using user-defined criteria.

    Parameters
    ----------
    start_date : str
        Start date in YYYY-MM-DD format.
    end_date : str
        End date in YYYY-MM-DD format.
    min_magnitude : float
        Minimum earthquake magnitude.
    latitude : float
        Latitude of the search centre.
    longitude : float
        Longitude of the search centre.
    radius_km : float
        Approximate search radius in kilometres.
    max_events : int or None
        Maximum number of events to return.
    """

    if min_magnitude < 0:
        raise ValueError("Minimum magnitude cannot be negative.")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if max_events is not None and max_events <= 0:
        raise ValueError("Number of events must be greater than 0.")

    start_time = UTCDateTime(
        f"{start_date}T00:00:00"
    )

    end_time = UTCDateTime(
        f"{end_date}T23:59:59"
    )

    if end_time < start_time:
        raise ValueError(
            "End date cannot be earlier than start date."
        )

    radius_degrees = km_to_degrees(radius_km)

    client = Client(FDSN_CLIENT)

    try:
        catalog = client.get_events(
            starttime=start_time,
            endtime=end_time,
            latitude=latitude,
            longitude=longitude,
            maxradius=radius_degrees,
            minmagnitude=min_magnitude,
            orderby="time-asc",
        )

        events = list(catalog)

    except FDSNNoDataException:
        events = []

    if max_events is not None:
        events = events[:max_events]

    return events


def get_event_information(event):
    """
    Extract useful information from an ObsPy Event.
    """
    origin = event.preferred_origin() or event.origins[0]
    magnitude = event.preferred_magnitude() or event.magnitudes[0]

    return {
        "time": origin.time,
        "latitude": origin.latitude,
        "longitude": origin.longitude,
        "depth_km": (
            origin.depth / 1000
            if origin.depth is not None
            else None
        ),
        "magnitude": magnitude.mag,
        "magnitude_type": magnitude.magnitude_type,
    }


def download_station_metadata(
    output_path,
    network=DEFAULT_NETWORK,
    station=DEFAULT_STATION,
    location=DEFAULT_LOCATION,
    channel=DEFAULT_CHANNEL,
):
    """
    Download station metadata including instrument response.
    """
    client = Client(FDSN_CLIENT)

    inventory = client.get_stations(
        network=network,
        station=station,
        location=location,
        channel=channel,
        level="response",
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    inventory.write(
        str(output_path),
        format="STATIONXML",
    )

    return inventory


def download_event_waveform(
    event,
    output_path,
    network=DEFAULT_NETWORK,
    station=DEFAULT_STATION,
    location=DEFAULT_LOCATION,
    channel=DEFAULT_CHANNEL,
):
    """
    Download a waveform around an earthquake origin time.
    """
    origin = event.preferred_origin() or event.origins[0]

    start_time = origin.time - PRE_EVENT_SECONDS
    end_time = origin.time + POST_EVENT_SECONDS

    client = Client(FDSN_CLIENT)

    stream = client.get_waveforms(
        network=network,
        station=station,
        location=location,
        channel=channel,
        starttime=start_time,
        endtime=end_time,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    stream.write(
        str(output_path),
        format="MSEED",
    )

    return stream