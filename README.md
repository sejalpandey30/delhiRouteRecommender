# Delhi Transit — Multimodal Route Planner

A real journey planner over Delhi's bus (DTC/DIMTS) + metro (DMRC) GTFS
feeds. Given an origin and destination stop/station and a departure time,
it finds the fastest journey, freely mixing bus and metro legs with
walking transfers between them (bus → metro → bus, or any other
combination the network actually supports).

## What's in the box

| File | Purpose |
|---|---|
| `gtfs_loader.py` | Loads both GTFS feeds and namespaces IDs so bus/metro stop numbers don't collide |
| `build_network.py` | Groups trips into RAPTOR "patterns", computes walking-transfer edges between nearby stops, caches everything to `cache/network.pkl` |
| `raptor.py` | The routing engine — a RAPTOR (Round-based Public Transit Optimized Router) implementation, plus stop search |
| `app.py` | Flask web app: search API + journey-planning API + the UI |
| `templates/index.html` | Single-page front end — search boxes with autocomplete, and a journey-diagram result view colored with the real DMRC line colors |
| `cache/network.pkl` | Prebuilt network — ships in this bundle so you can run the app immediately without reprocessing 3.8M rows |

## Quick start

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5050**. The prebuilt `cache/network.pkl` is
included, so this works immediately — you don't need to re-run
`build_network.py` unless you want to rebuild from fresh GTFS data.

## Rebuilding the network from your own GTFS data

If DTC/DIMTS or DMRC publish an updated feed, drop the new files in and
rebuild:

```bash
# unzip your GTFS feeds so the folders look like:
#   gtfs/bus/{agency,calendar,routes,stops,trips,stop_times}.txt
#   gtfs/metro/{agency,calendar,routes,stops,trips,stop_times}.txt
python build_network.py
python app.py
```

Paths are configurable via environment variables if you'd rather keep the
feeds elsewhere:

```bash
export BUS_GTFS_DIR=/path/to/bus/gtfs
export METRO_GTFS_DIR=/path/to/metro/gtfs
export NETWORK_CACHE_PATH=/path/to/cache/network.pkl
python build_network.py
```

## How the routing works

This is a from-scratch **RAPTOR** implementation, the algorithm real
multimodal trip planners are built on (it's what OpenTripPlanner-style
systems use under the hood):

1. **Patterns, not raw trips.** GTFS `trips.txt` has ~95K individual trips,
   but many share an identical stop sequence (e.g. all "708 DOWN" runs
   throughout the day). These are grouped into ~2,400 *patterns*, so a
   round of the algorithm scans each *pattern* once rather than every trip.
2. **Rounds = number of transit legs.** Round *k* computes the earliest
   arrival time at every stop using at most *k* transit legs. This is what
   lets it find A→bus→B→metro→C→bus→D journeys — each mode switch is just
   another round.
3. **Walking transfers.** There's no `transfers.txt` in either feed, so
   transfer edges are computed directly from stop coordinates: any two
   stops (bus↔bus, bus↔metro, metro↔metro) within ~350m straight-line are
   linked, with walk time = distance × a 1.4 street-detour factor ÷
   walking speed. This is what lets you get off a bus a block from a metro
   station and have the planner know you can walk it.
4. A round terminates when no stop's arrival time improves; results are
   reconstructed into legs (which trip, which route, board/alight stop and
   time, or a walk).

## Known limitations (worth knowing before you trust it for something important)

- **Walking transfers are straight-line, not street-network.** There's no
  OpenStreetMap/sidewalk data here, so a transfer that looks like 350m on
  the map might be blocked by a highway, railway, or river in reality. The
  1.4x detour factor and 350m cap are a rough correction, not a real
  routing engine (integrating OSRM/OSM walking data would fix this
  properly).
- **No live delays/disruptions.** This plans against the static published
  schedule only.
- **No fare calculation.** `fare_attributes.txt`/`fare_rules.txt` were
  intentionally skipped (they're huge and not needed for the routing
  itself) — this only optimizes for arrival time, not cost.
- **Single-criterion optimization.** It finds the earliest arrival; it
  doesn't yet offer a "fewest transfers" or "least walking" alternative.
- **Calendar/service_id isn't filtered by day of week.** All trips are
  currently treated as always running — a weekday-only metro trip could in
  principle be offered on a Sunday query. Worth fixing if you plan to rely
  on this for actual trip planning (join against `calendar.txt`'s day
  columns).

## Extending it

- Multi-criteria RAPTOR (Pareto-optimal on arrival time *and* transfers)
  is a natural next step — the paper it's based on already defines this.
- Swap the straight-line footpaths for an OSRM walking-network call.
- Add day-of-week / service calendar filtering (see limitation above).
- Add a live "next departures" board per stop using the same pattern data.
