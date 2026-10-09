# Delhi Transit — Multimodal Route Planner

The fastest and most reliable way to navigate Delhi's public transportation network.

Delhi Transit is an open-source journey planner that routes across Delhi's metro, bus network, and walking transfers. It uses a custom RAPTOR-based routing engine to find efficient multimodal journeys between any two points in the city.

Live demo: https://delhi-route-recommender--sejalpandey30.replit.app

---

## Overview

This application combines Delhi's bus and metro schedules into a single route-planning system. A user can enter an origin, destination, and departure time, and the system returns the fastest available multimodal route, including bus-to-metro, metro-to-bus, and walking transfers between nearby stops.

The project is designed for use as a public-facing transit tool, a research prototype, and a developer-focused routing engine.

---

## Key Features

- Multimodal route planning across bus, metro, and walking
- Fast journey computation using a RAPTOR-based engine
- Interactive map interface with real-time styled route visualization
- Search history and saved favorite routes
- Prebuilt network cache for immediate startup without rebuilding GTFS data
- Support for stop-level autocomplete and route detail rendering

---

## Live Application

The deployed public version is available here:

https://delhi-route-recommender--sejalpandey30.replit.app

---

## Quick Start

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

The repository includes a prebuilt network cache at `cache/network.pkl`, so the app runs immediately without requiring GTFS reconstruction unless you want to rebuild the network from scratch.

---

## How to Use

1. Enter an origin stop or station.
2. Enter a destination stop or station.
3. Choose a departure time.
4. Click the route button to generate the best journey.
5. Review the route timeline, transfer count, total duration, and map path.
6. Save the route to favorites or revisit recent searches.

---

## Architecture

### Backend

- Flask web application
- SQLite database for user history and saved routes
- REST API for stop search, route planning, history, and favorites
- Custom RAPTOR-based routing engine

### Frontend

- HTML, CSS, and JavaScript single-page interface
- Leaflet map rendering with OpenStreetMap tiles
- Search autocomplete, route cards, and stop markers

### Data model

- GTFS-based transit network data
- Stop-level route and transfer graph
- Serialized network cache for fast startup

---

## API Endpoints

### Route planning

- `GET /api/search?q=<query>`
  Search for stops by name.

- `GET /api/plan?origin=<idx>&dest=<idx>&time=<HH:MM>`
  Returns the best multimodal route.

- `GET /api/stops/<idx>`
  Returns lat/lon coordinates for a stop.

### History

- `GET /api/history`
  Fetch recent searches.

- `DELETE /api/history/<id>`
  Delete a single search entry.

- `DELETE /api/history/clear`
  Clear all search history.

### Favorites

- `GET /api/favourites`
  Fetch saved routes.

- `POST /api/favourites`
  Save a route.

- `DELETE /api/favourites/<id>`
  Delete a saved route.

---

## Routing Approach

This project implements RAPTOR (Round-based Public Transit Optimized Router), a routing algorithm designed for large transit networks.

The routing process works as follows:

1. GTFS trips are grouped into route patterns with identical stop sequences.
2. Each round scans patterns and updates best transit arrivals across the network.
3. Walking connections between nearby stops are added as transfer edges.
4. The algorithm reconstructs the journey into individual travel legs.

This allows the system to handle large city-scale route planning efficiently while supporting multimodal journeys.

---

## Project Structure

```text
.
├── app.py                  # Flask app and API routes
├── raptor.py               # RAPTOR routing engine
├── build_network.py        # GTFS processing and network cache generation
├── gtfs_loader.py          # GTFS parsing and normalization
├── requirements.txt        # Python dependencies
├── cache/
│   └── network.pkl         # Prebuilt routing network
├── templates/
│   └── index.html          # Frontend UI
├── data/
│   └── transit.db          # SQLite history/favorites database
├── README.md               # Project documentation
└── LICENSE                 # License file
```

---

## Updating GTFS and Rebuilding the Network

To rebuild the routing network from fresh transit data:

```bash
python build_network.py
python app.py
```

Recommended GTFS folder structure:

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

## Known Limitations

- Walking transfers are estimated from straight-line distance and are not based on a street-network model.
- The planner uses static schedule data and does not include live service disruptions or delays.
- Fare calculation is not implemented.
- The system optimizes primarily for earliest arrival time rather than lowest fare or fewest transfers.
- Calendar/service filtering is not yet fully applied.

These limitations are acknowledged and are natural next steps for future enhancement.

---

## Future Improvements

Planned developments include:

- Multi-criteria routing with alternatives such as fewest transfers and least walking
- Real-time transit updates and disruption handling
- Street-network walking transfers using OSRM or similar services
- Day-of-week and service calendar filtering
- Better fare and pricing integration
- Improved mobile and accessibility support

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
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
