# Delhi Transit — Multimodal Route Planner

Delhi's commute, sorted.

Delhi Transit is a production-ready, open-source journey planner built for one problem that affects millions of people every day: figuring out the fastest way to move across the city without turning your trip into a guessing game.

It combines Delhi's metro, bus network, and walking transfers into a single route-planning system. Instead of checking three different apps and hoping for the best, you can search an origin, destination, and departure time and get a smarter route recommendation in return.

Live demo: https://delhi-route-recommender--sejalpandey30.replit.app

---

## Why this project exists

A city like Delhi moves fast, but the commute can feel chaotic.

This project exists to make that experience simpler: a single interface for planning multimodal journeys across metro, bus, and walking transfers. Whether you're heading to work, university, or a meeting across town, the app helps you find a route that is faster, clearer, and easier to follow.

---

## What it does

- Finds optimal multimodal routes across Delhi's metro and bus network
- Mixes bus, metro, and walking in a single journey plan
- Shows route details such as boarding stops, transfer points, and travel time
- Displays the trip on an interactive map for easier decision-making
- Remembers your recent searches and saves favorite routes

In short: less zig-zagging across city maps, more straightforward route planning.

---

## Key features

- Multimodal route planning across bus, metro, and walking
- Fast journey computation using a RAPTOR-based routing engine
- Interactive map interface with styled route visualization
- Search history and saved favorite routes
- Prebuilt network cache for immediate startup without requiring a full GTFS rebuild
- Stop search with autocomplete for quick navigation

---

## Live application

You can use the public deployment here:

https://delhi-route-recommender--sejalpandey30.replit.app

---

## Quick start

### Local setup

Requirements: Python 3.8+

```bash
git clone https://github.com/sejalpandey30/delhiRouteRecommender.git
cd delhiRouteRecommender
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://localhost:5050
```

The repository includes a prebuilt network cache at `cache/network.pkl`, so the app works immediately without rebuilding GTFS data unless you want to regenerate the network from scratch.

---

## How to use

1. Enter an origin stop or station.
2. Enter a destination stop or station.
3. Select a departure time.
4. Click the route button.
5. Review the route, transfer count, duration, and map path.
6. Save useful routes or revisit recent searches.

It is designed to feel simple for everyday travel planning, without losing the technical depth underneath the hood.

---

## Architecture

### Backend

- Flask application server
- SQLite database for recent searches and saved favorite routes
- REST API for route planning, search, and route persistence
- Custom RAPTOR-based transit routing engine

### Frontend

- HTML, CSS, and JavaScript interface
- Leaflet-based map rendering with OpenStreetMap tiles
- Search suggestions and route cards for trip summaries

### Data pipeline

- GTFS-based transit data ingestion
- Stop-level route graph creation
- Serialized network cache for efficient startup and repeated planning

---

## API endpoints

### Route planning

- `GET /api/search?q=<query>`
  Search available stops by name.

- `GET /api/plan?origin=<idx>&dest=<idx>&time=<HH:MM>`
  Return the best route for the chosen trip.

- `GET /api/stops/<idx>`
  Return latitude and longitude for a stop.

### Search history

- `GET /api/history`
  Fetch recent searches.

- `DELETE /api/history/<id>`
  Remove a single route history entry.

- `DELETE /api/history/clear`
  Clear all history.

### Favorite routes

- `GET /api/favourites`
  Fetch saved routes.

- `POST /api/favourites`
  Save a route.

- `DELETE /api/favourites/<id>`
  Delete a saved route.

---

## Routing approach

This project uses RAPTOR (Round-based Public Transit Optimized Router), a routing method built for large-scale public transit networks.

The logic works like this:

1. GTFS trips are grouped into patterns that share the same stop sequence.
2. Each round scans those patterns to find improved arrivals across the network.
3. Nearby stops are linked through walking transfer edges.
4. The system reconstructs the final journey into transit and walking segments.

This approach is much more efficient than processing every single trip as a separate route edge.

---

## Project structure

```text
.
├── app.py                  # Flask app and API routes
├── raptor.py               # RAPTOR routing engine
├── build_network.py        # GTFS processing and cache generation
├── gtfs_loader.py          # GTFS parsing and normalization
├── requirements.txt        # Python dependencies
├── cache/
│   └── network.pkl         # Prebuilt routing network
├── templates/
│   └── index.html          # Frontend UI
├── data/
│   └── transit.db          # SQLite database for history and favorites
├── README.md               # Project documentation
└── LICENSE                 # License file
```

---

## Rebuilding the network

If you want to rebuild the route network from the latest GTFS feeds:

```bash
python build_network.py
python app.py
```

Typical GTFS structure:

```text
gtfs/
├── bus/
│   ├── agency.txt
│   ├── calendar.txt
│   ├── routes.txt
│   ├── stops.txt
│   ├── trips.txt
│   └── stop_times.txt
└── metro/
    ├── agency.txt
    ├── calendar.txt
    ├── routes.txt
    ├── stops.txt
    ├── trips.txt
    └── stop_times.txt
```

Optional environment configuration:

```bash
export BUS_GTFS_DIR=/path/to/bus/gtfs
export METRO_GTFS_DIR=/path/to/metro/gtfs
export NETWORK_CACHE_PATH=/path/to/cache/network.pkl
python build_network.py
```

---

## Known limitations

- Walking transfers are estimated using straight-line distance, not a full street-network model.
- The app uses static schedule data and does not include live disruptions or delays.
- Fare calculation is not implemented.
- The route engine currently prioritizes earliest arrival time over other optimization criteria.
- Calendar filtering is not yet fully enforced.

These are honest trade-offs that keep the project lightweight and fast, while leaving room for future enhancements.

---

## Future improvements

Planned enhancements include:

- Multi-criteria routing with alternatives such as fewest transfers and least walking
- Real-time transit updates and delay handling
- More realistic walking transfers using a street-network model
- Day-of-week and service calendar filtering
- Better fare and pricing integration
- Improved mobile and accessibility support

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a pull request.

---

## References

- RAPTOR paper: https://research.microsoft.com/en-us/um/people/seidenbe/papers/raptor_alenex.pdf
- GTFS specification: https://gtfs.org/
- DMRC: https://delhimetrorail.com/
- DTC/DIMTS: https://www.dtc.nic.in/

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Author

Sejal Pandey
