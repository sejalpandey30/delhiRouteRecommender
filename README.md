# 🚇 Delhi Transit — Multimodal Route Planner

Delhi's commute, sorted.

Delhi Transit is a production-ready route planner that helps people move across Delhi by combining metro, bus, and walking transfers into one simple journey-planning tool.

Live demo: https://delhi-route-recommender--sejalpandey30.replit.app

## What it does

- Finds the fastest multimodal route between any two stops or stations
- Combines metro, bus, and walking into one trip
- Shows boarding/alighting stops, transfer details, and route summary
- Displays the route on an interactive map
- Saves recent searches and favorite journeys

## Quick start

```bash
git clone https://github.com/sejalpandey30/delhiRouteRecommender.git
cd delhiRouteRecommender
pip install -r requirements.txt
python app.py
```

Open: http://localhost:5050

## Why this project

Delhi's public transport is vast and often fragmented. This project brings it together in one interface so users can plan a trip without checking multiple systems or maps.

## Tech stack

- Flask for the backend and API
- SQLite for search history and saved routes
- Leaflet + OpenStreetMap for the map view
- RAPTOR-based routing engine for efficient multimodal route finding

## Project structure

```text
.
├── app.py
├── raptor.py
├── build_network.py
├── gtfs_loader.py
├── requirements.txt
├── cache/
│   └── network.pkl
├── templates/
│   └── index.html
├── data/
│   └── transit.db
├── README.md
└── LICENSE
```

## Notes

- Walking transfers are estimated rather than street-network exact.
- The app uses static schedule data, not live delay feeds.
- It currently optimizes for fastest route rather than fare or minimum transfers.

## Contributing

Contributions are welcome.

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## References

- RAPTOR paper: https://research.microsoft.com/en-us/um/people/seidenbe/papers/raptor_alenex.pdf
- GTFS: https://gtfs.org/
- DMRC: https://delhimetrorail.com/
- DTC/DIMTS: https://www.dtc.nic.in/

---

Built for better daily commutes in Delhi.

© 2026 Sejal Pandey
