"""
Builds the compact, RAPTOR-ready network structures from the merged GTFS
tables and caches them to disk (pickle) so the web app / CLI doesn't have
to reprocess 3.8M stop_times rows on every start.

Key RAPTOR concept: trips must be grouped into "patterns" -- sets of trips
that visit the exact same ordered sequence of stops. Within a pattern, trips
never overtake each other, which is what lets RAPTOR scan a pattern in O(stops)
per round instead of doing per-trip Dijkstra relaxations.
"""
import os
import pickle
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from collections import defaultdict

from gtfs_loader import load_all

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.environ.get("NETWORK_CACHE_PATH", os.path.join(BASE_DIR, "cache", "network.pkl"))

WALK_SPEED_MPS = 1.25          # ~4.5 km/h average walking speed
MAX_TRANSFER_METERS = 350      # only link stops within this straight-line radius
MIN_TRANSFER_SECONDS = 60      # minimum dwell/transfer buffer at any interchange
DETOUR_FACTOR = 1.4            # streets/sidewalks aren't straight lines; no OSM data here,
                                # so inflate euclidean distance to approximate real walk distance
EARTH_RADIUS_M = 6371000.0


def latlon_to_local_xy(lat, lon, lat0):
    """Equirectangular projection -- fine for a city-sized area like Delhi NCR."""
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    lat0_rad = np.radians(lat0)
    x = EARTH_RADIUS_M * lon_rad * np.cos(lat0_rad)
    y = EARTH_RADIUS_M * lat_rad
    return x, y


def build_network():
    stops, trips, stop_times, routes = load_all()

    # ---- unified integer stop index ----
    stops = stops.drop_duplicates(subset="stop_id").reset_index(drop=True)
    stop_id_to_idx = {sid: i for i, sid in enumerate(stops["stop_id"])}
    n_stops = len(stops)
    stop_names = stops["stop_name"].to_numpy()
    stop_lats = stops["stop_lat"].to_numpy()
    stop_lons = stops["stop_lon"].to_numpy()
    stop_modes = stops["mode"].to_numpy()

    # ---- attach route info (mode, display name) to trips ----
    route_lookup = routes.set_index("route_id")[["route_short_name", "route_long_name", "mode"]].to_dict("index")

    # ---- group stop_times by trip, build stop-sequence signature per trip ----
    stop_times = stop_times[stop_times["stop_id"].isin(stop_id_to_idx)]
    stop_times["stop_idx"] = stop_times["stop_id"].map(stop_id_to_idx)

    grouped = stop_times.groupby("trip_id", sort=False)

    pattern_map = {}          # signature tuple -> pattern_id
    pattern_stop_seq = []     # pattern_id -> list[stop_idx]
    pattern_trips = defaultdict(list)   # pattern_id -> list of (trip_id, arr[], dep[])
    trip_route_mode = {}      # trip_id -> (route_id, mode)

    trips_indexed = trips.set_index("trip_id")

    skipped = 0
    for trip_id, g in grouped:
        g = g.sort_values("stop_sequence")
        seq = tuple(g["stop_idx"].tolist())
        if len(seq) < 2:
            skipped += 1
            continue
        if seq not in pattern_map:
            pattern_map[seq] = len(pattern_stop_seq)
            pattern_stop_seq.append(list(seq))
        pid = pattern_map[seq]

        try:
            route_id = trips_indexed.at[trip_id, "route_id"]
            mode = trips_indexed.at[trip_id, "mode"]
        except KeyError:
            skipped += 1
            continue

        arr = g["arrival_sec"].to_numpy(dtype=np.int32)
        dep = g["departure_sec"].to_numpy(dtype=np.int32)
        pattern_trips[pid].append((trip_id, route_id, mode, arr, dep))
        trip_route_mode[trip_id] = (route_id, mode)

    # sort trips within each pattern by departure time at first stop (RAPTOR requirement)
    for pid in pattern_trips:
        pattern_trips[pid].sort(key=lambda t: t[4][0])

    # ---- build stop -> list of (pattern_id, position_in_pattern) ----
    stop_to_patterns = defaultdict(list)
    for pid, seq in enumerate(pattern_stop_seq):
        for pos, s_idx in enumerate(seq):
            stop_to_patterns[s_idx].append((pid, pos))

    # ---- footpath transfers via KDTree (bus<->bus, bus<->metro, metro<->metro) ----
    lat0 = float(np.mean(stop_lats))
    xs, ys = latlon_to_local_xy(stop_lats, stop_lons, lat0)
    coords = np.column_stack([xs, ys])
    tree = cKDTree(coords)
    pairs = tree.query_pairs(r=MAX_TRANSFER_METERS, output_type="ndarray")

    footpaths = defaultdict(list)  # stop_idx -> list of (other_stop_idx, walk_seconds)
    for i, j in pairs:
        dist = np.hypot(xs[i] - xs[j], ys[i] - ys[j]) * DETOUR_FACTOR
        walk_sec = max(MIN_TRANSFER_SECONDS, int(dist / WALK_SPEED_MPS))
        footpaths[i].append((int(j), walk_sec))
        footpaths[j].append((int(i), walk_sec))

    network = {
        "n_stops": n_stops,
        "stop_id_to_idx": stop_id_to_idx,
        "stop_ids": stops["stop_id"].to_numpy(),
        "stop_names": stop_names,
        "stop_lats": stop_lats,
        "stop_lons": stop_lons,
        "stop_modes": stop_modes,
        "pattern_stop_seq": pattern_stop_seq,
        "pattern_trips": dict(pattern_trips),
        "stop_to_patterns": dict(stop_to_patterns),
        "footpaths": dict(footpaths),
        "route_lookup": route_lookup,
    }

    print(f"stops={n_stops} patterns={len(pattern_stop_seq)} "
          f"trips_used={sum(len(v) for v in pattern_trips.values())} skipped_trips={skipped} "
          f"footpath_pairs={len(pairs)}")
    return network


if __name__ == "__main__":
    net = build_network()
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(net, f, protocol=pickle.HIGHEST_PROTOCOL)
    print("cached to", CACHE_PATH)
