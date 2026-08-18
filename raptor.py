"""
RAPTOR (Round-based Public Transit Optimized Router) journey planner.

Handles bus -> metro -> bus (or any mix, any number of legs) journeys over
the merged Delhi bus + metro network, including walking transfers between
nearby stops of different modes.

Algorithm sketch (per Delling/Pyrga/Werneck/Wagner's RAPTOR paper):
  - Round k finds the earliest arrival time at every stop using at most k
    transit legs (trips).
  - Each round: for every "route pattern" touched by a stop improved in the
    previous round, scan the pattern's stops in order once, boarding the
    earliest trip that's still catchable, and relax arrival times.
  - After the transit scan, relax footpath (walking) transfers.
  - Stop when a round makes no further improvements, or after a round cap.

This avoids per-trip Dijkstra edges (there could be millions) and instead
does O(rounds x patterns x stops_in_pattern), which is fast even on a
network this size.
"""
import os
import pickle
import numpy as np
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.environ.get("NETWORK_CACHE_PATH", os.path.join(BASE_DIR, "cache", "network.pkl"))
MAX_ROUNDS = 6
INF = 10 ** 9


class Network:
    def __init__(self, path=CACHE_PATH):
        with open(path, "rb") as f:
            net = pickle.load(f)
        self.n_stops = net["n_stops"]
        self.stop_id_to_idx = net["stop_id_to_idx"]
        self.stop_ids = net["stop_ids"]
        self.stop_names = net["stop_names"]
        self.stop_lats = net["stop_lats"]
        self.stop_lons = net["stop_lons"]
        self.stop_modes = net["stop_modes"]
        self.pattern_stop_seq = net["pattern_stop_seq"]
        self.pattern_trips = net["pattern_trips"]
        self.stop_to_patterns = net["stop_to_patterns"]
        self.footpaths = net["footpaths"]
        self.route_lookup = net["route_lookup"]

        # name -> [stop_idx,...] for search / autocomplete
        self.name_index = defaultdict(list)
        for idx, name in enumerate(self.stop_names):
            self.name_index[name.strip().lower()].append(idx)

    def search_stops(self, query, limit=15):
        q = query.strip().lower()
        if not q:
            return []
        seen_names = set()
        results = []
        for idx, name in enumerate(self.stop_names):
            if q in name.lower():
                key = (name, self.stop_modes[idx])
                if key in seen_names:
                    continue
                seen_names.add(key)
                results.append({
                    "stop_idx": int(idx),
                    "stop_id": self.stop_ids[idx],
                    "name": name,
                    "mode": self.stop_modes[idx],
                    "lat": float(self.stop_lats[idx]),
                    "lon": float(self.stop_lons[idx]),
                })
                if len(results) >= limit:
                    break
        return results


class RaptorRouter:
    def __init__(self, network: Network):
        self.net = network

    def plan(self, origin_idx, dest_idx, departure_sec, max_rounds=MAX_ROUNDS):
        net = self.net
        n = net.n_stops

        best_arrival = np.full(n, INF, dtype=np.int64)
        best_arrival[origin_idx] = departure_sec

        # per-round arrival snapshots, and parent pointers for reconstruction
        # parent[stop] = (kind, ...) where kind is 'trip' or 'walk' or 'start'
        parent = {origin_idx: ("start", None, None, None, departure_sec)}

        marked = {origin_idx}
        round_arrival = best_arrival.copy()

        for rnd in range(1, max_rounds + 1):
            new_round_arrival = round_arrival.copy()

            # collect patterns touched by marked stops
            patterns_to_scan = defaultdict(int)  # pattern_id -> earliest position to start scan from
            for s in marked:
                for pid, pos in net.stop_to_patterns.get(s, []):
                    if pid not in patterns_to_scan or pos < patterns_to_scan[pid]:
                        patterns_to_scan[pid] = pos

            newly_marked = set()

            for pid, start_pos in patterns_to_scan.items():
                seq = net.pattern_stop_seq[pid]
                trip_list = net.pattern_trips[pid]  # sorted by departure at stop 0... but we board at start_pos
                boarded_trip = None   # (trip_id, route_id, mode, arr, dep)
                boarded_at_stop = None
                boarded_at_time = None

                for pos in range(start_pos, len(seq)):
                    s_idx = seq[pos]

                    if boarded_trip is not None:
                        arr_time = int(boarded_trip[3][pos])
                        if arr_time < new_round_arrival[s_idx] and arr_time < best_arrival[s_idx]:
                            new_round_arrival[s_idx] = arr_time
                            best_arrival[s_idx] = arr_time
                            parent[s_idx] = (
                                "trip", boarded_trip[0], boarded_trip[1], boarded_trip[2],
                                boarded_at_stop, boarded_at_time, arr_time, pid
                            )
                            newly_marked.add(s_idx)

                    # can we catch an earlier (or first) trip here?
                    # rider is at stop s_idx no earlier than round_arrival[s_idx] (prev round's best)
                    avail_time = round_arrival[s_idx]
                    if avail_time < INF:
                        if boarded_trip is None:
                            candidate_dep = avail_time
                        else:
                            candidate_dep = None

                        if boarded_trip is None or True:
                            # try to find an earlier trip at this stop than current boarded_trip
                            best_dep = None
                            for t in trip_list:
                                dep_here = int(t[4][pos])
                                if dep_here >= avail_time:
                                    if boarded_trip is None or dep_here < int(boarded_trip[4][pos]):
                                        best_dep = t
                                    break  # trip_list sorted by dep at stop0; within-pattern trips don't overtake
                            if best_dep is not None:
                                boarded_trip = best_dep
                                boarded_at_stop = s_idx
                                boarded_at_time = int(best_dep[4][pos])

            marked = newly_marked

            # ---- relax footpaths from newly improved stops ----
            walk_marked = set()
            for s in list(newly_marked):
                t_s = new_round_arrival[s]
                for (other, walk_sec) in net.footpaths.get(s, []):
                    cand = t_s + walk_sec
                    if cand < new_round_arrival[other] and cand < best_arrival[other]:
                        new_round_arrival[other] = cand
                        best_arrival[other] = cand
                        parent[other] = ("walk", s, walk_sec, None, None, None, cand, None)
                        walk_marked.add(other)

            marked |= walk_marked
            round_arrival = new_round_arrival

            if not marked:
                break

        if best_arrival[dest_idx] >= INF:
            return None

        return self._reconstruct(origin_idx, dest_idx, parent, best_arrival[dest_idx])

    def _reconstruct(self, origin_idx, dest_idx, parent, arrival_time):
        net = self.net
        legs = []
        cur = dest_idx
        chain = []
        while cur != origin_idx:
            p = parent[cur]
            chain.append((cur, p))
            if p[0] == "trip":
                cur = p[4]  # boarded_at_stop
            elif p[0] == "walk":
                cur = p[1]
            else:
                break
        chain.reverse()

        # merge consecutive 'trip' hops that share the same trip_id into one leg
        legs = []
        i = 0
        while i < len(chain):
            stop_idx, p = chain[i]
            if p[0] == "trip":
                trip_id, route_id, mode = p[1], p[2], p[3]
                board_stop, board_time = p[4], p[5]
                alight_stop, alight_time = stop_idx, p[6]
                j = i + 1
                while j < len(chain) and chain[j][1][0] == "trip" and chain[j][1][1] == trip_id:
                    alight_stop, alight_time = chain[j][0], chain[j][1][6]
                    j += 1
                route_info = net.route_lookup.get(route_id, {})
                legs.append({
                    "type": "transit",
                    "mode": mode,
                    "route_short_name": route_info.get("route_short_name", ""),
                    "route_long_name": route_info.get("route_long_name", ""),
                    "board_stop": net.stop_names[board_stop],
                    "board_time": board_time,
                    "alight_stop": net.stop_names[alight_stop],
                    "alight_time": alight_time,
                })
                i = j
            elif p[0] == "walk":
                from_stop = p[1]
                walk_sec = p[2]
                legs.append({
                    "type": "walk",
                    "from_stop": net.stop_names[from_stop],
                    "to_stop": net.stop_names[stop_idx],
                    "walk_seconds": walk_sec,
                })
                i += 1
            else:
                i += 1

        return {
            "arrival_time": int(arrival_time),
            "legs": legs,
        }


def fmt_time(sec):
    sec = int(sec) % (24 * 3600)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}"


if __name__ == "__main__":
    net = Network()
    router = RaptorRouter(net)

    # quick smoke test: pick two stops far apart and route between them
    print("Loaded", net.n_stops, "stops")
