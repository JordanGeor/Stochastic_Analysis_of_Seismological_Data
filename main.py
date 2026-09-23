from seismic_analysis.acquisition import (
    search_events,
    get_event_information,
)


def get_date(prompt):
    while True:
        value = input(prompt).strip()

        try:
            parts = value.split("-")

            if len(parts) != 3:
                raise ValueError

            year, month, day = map(int, parts)

            if (
                year < 1900
                or month < 1
                or month > 12
                or day < 1
                or day > 31
            ):
                raise ValueError

            return value

        except ValueError:
            print(
                "Invalid date. "
                "Use the format YYYY-MM-DD."
            )


def get_float(prompt, minimum=None, maximum=None):
    while True:
        try:
            value = float(input(prompt).strip())

            if minimum is not None and value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            if maximum is not None and value > maximum:
                print(f"Value must not exceed {maximum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid number.")


def get_integer(prompt, minimum=1):
    while True:
        try:
            value = int(input(prompt).strip())

            if value < minimum:
                print(
                    f"Value must be at least {minimum}."
                )
                continue

            return value

        except ValueError:
            print("Please enter a whole number.")


def display_events(events):
    print("\n" + "=" * 78)
    print("EARTHQUAKES FOUND")
    print("=" * 78)

    if not events:
        print("No earthquakes matched the search criteria.")
        return

    for index, event in enumerate(events, start=1):
        info = get_event_information(event)

        depth = info["depth_km"]

        if depth is None:
            depth_text = "N/A"
        else:
            depth_text = f"{depth:.1f} km"

        magnitude_type = info["magnitude_type"] or ""

        print(
            f"{index:>3}. "
            f"{info['time']} | "
            f"M {info['magnitude']:.2f} "
            f"{magnitude_type} | "
            f"Lat {info['latitude']:.3f} | "
            f"Lon {info['longitude']:.3f} | "
            f"Depth {depth_text}"
        )

    print("=" * 78)


def main():
    print("\n" + "=" * 55)
    print(" STOCHASTIC ANALYSIS OF SEISMOLOGICAL DATA")
    print("=" * 55)

    print("\nEarthquake Search\n")

    start_date = get_date(
        "Start date (YYYY-MM-DD): "
    )

    end_date = get_date(
        "End date (YYYY-MM-DD): "
    )

    min_magnitude = get_float(
        "Minimum magnitude: ",
        minimum=0,
    )

    latitude = get_float(
        "Center latitude (-90 to 90): ",
        minimum=-90,
        maximum=90,
    )

    longitude = get_float(
        "Center longitude (-180 to 180): ",
        minimum=-180,
        maximum=180,
    )

    radius_km = get_float(
        "Search radius (km): ",
        minimum=0.1,
    )

    print("\nSearching NOA earthquake catalog...")

    try:
        events = search_events(
            start_date=start_date,
            end_date=end_date,
            min_magnitude=min_magnitude,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

    except Exception as error:
        print(f"\nSearch failed: {error}")
        return

    print(
        f"\nFound {len(events)} earthquake(s)."
    )

    display_events(events)

    if not events:
        return

    print(
        f"\nA total of {len(events)} earthquake(s) "
        "match your search criteria."
    )

    while True:
        selection = input(
            "\nEnter earthquake numbers to analyze "
            "(example: 1,3,5) or type 'all': "
        ).strip()

        if selection.lower() == "all":
            selected_events = events
            break

        try:
            indices = [
                int(value.strip())
                for value in selection.split(",")
            ]

            if not indices:
                raise ValueError

            if any(
                index < 1 or index > len(events)
                for index in indices
            ):
                print(
                    f"Please choose numbers between "
                    f"1 and {len(events)}."
                )
                continue

            # Remove duplicate selections while
            # preserving the user's order.
            indices = list(dict.fromkeys(indices))

            selected_events = [
                events[index - 1]
                for index in indices
            ]

            break

        except ValueError:
            print(
                "Invalid selection. "
                "Example: 1,3,5 or all"
            )

    print(
        f"\n{len(selected_events)} earthquake(s) "
        "selected for analysis."
    )


if __name__ == "__main__":
    main()