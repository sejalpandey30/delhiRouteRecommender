"""
Loads the DTC/DIMTS bus GTFS feed and the DMRC metro GTFS feed, namespaces
their IDs so they don't collide, and merges them into one unified set of
stops / trips / stop_times / routes.
"""
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUS_DIR = os.environ.get("BUS_GTFS_DIR", os.path.join(BASE_DIR, "gtfs", "bus"))
METRO_DIR = os.environ.get("METRO_GTFS_DIR", os.path.join(BASE_DIR, "gtfs", "metro"))


def _hms_to_seconds(series):
    """Convert HH:MM:SS (GTFS allows >24:00:00 for post-midnight trips) to seconds."""
    parts = series.str.split(":", expand=True).astype(int)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def load_feed(gtfs_dir, mode, prefix):
    """Load one GTFS feed's essential tables and namespace all ids with `prefix`."""
    stops = pd.read_csv(f"{gtfs_dir}/stops.txt", dtype=str)
    trips = pd.read_csv(f"{gtfs_dir}/trips.txt", dtype=str)
    stop_times = pd.read_csv(
        f"{gtfs_dir}/stop_times.txt",
        dtype=str,
        usecols=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
    )
    routes = pd.read_csv(f"{gtfs_dir}/routes.txt", dtype=str)

    stops["stop_id"] = prefix + stops["stop_id"]
    trips["trip_id"] = prefix + trips["trip_id"]
    trips["route_id"] = prefix + trips["route_id"]
    stop_times["trip_id"] = prefix + stop_times["trip_id"]
    stop_times["stop_id"] = prefix + stop_times["stop_id"]
    routes["route_id"] = prefix + routes["route_id"]

    stops["stop_lat"] = stops["stop_lat"].astype(float)
    stops["stop_lon"] = stops["stop_lon"].astype(float)
    stops["mode"] = mode

    stop_times["stop_sequence"] = stop_times["stop_sequence"].astype(int)
    stop_times["arrival_sec"] = _hms_to_seconds(stop_times["arrival_time"])
    stop_times["departure_sec"] = _hms_to_seconds(stop_times["departure_time"])

    trips["mode"] = mode
    routes["mode"] = mode
    if "route_short_name" not in routes.columns:
        routes["route_short_name"] = ""
    if "route_long_name" not in routes.columns:
        routes["route_long_name"] = ""
    routes["route_short_name"] = routes["route_short_name"].fillna("")
    routes["route_long_name"] = routes["route_long_name"].fillna("")

    return stops, trips, stop_times, routes


def load_all():
    bus_stops, bus_trips, bus_st, bus_routes = load_feed(BUS_DIR, "bus", "B_")
    metro_stops, metro_trips, metro_st, metro_routes = load_feed(METRO_DIR, "metro", "M_")

    stops = pd.concat(
        [bus_stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "mode"]],
         metro_stops[["stop_id", "stop_name", "stop_lat", "stop_lon", "mode"]]],
        ignore_index=True,
    )
    trips = pd.concat(
        [bus_trips[["trip_id", "route_id", "service_id", "mode"]],
         metro_trips[["trip_id", "route_id", "service_id", "mode"]]],
        ignore_index=True,
    )
    stop_times = pd.concat([bus_st, metro_st], ignore_index=True)
    routes = pd.concat(
        [bus_routes[["route_id", "route_short_name", "route_long_name", "mode"]],
         metro_routes[["route_id", "route_short_name", "route_long_name", "mode"]]],
        ignore_index=True,
    )

    stop_times = stop_times.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
    return stops, trips, stop_times, routes


if __name__ == "__main__":
    stops, trips, stop_times, routes = load_all()
    print("stops:", len(stops))
    print("trips:", len(trips))
    print("stop_times:", len(stop_times))
    print("routes:", len(routes))
    print(stops["mode"].value_counts())
