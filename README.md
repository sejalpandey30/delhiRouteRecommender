# 🚇 Delhi Transit — Multimodal Route Planner

Delhi's commute, sorted.

Delhi Transit is a production-ready open-source journey planner built to help people move across Delhi without juggling multiple apps and scattered maps. It combines bus, metro, and walking transfers into one simple route-planning experience.

Live demo: https://delhi-route-recommender--sejalpandey30.replit.app

---

## ✨ What it does

- Plans routes across Delhi's metro and bus network
- Mixes bus, metro, and walking into a single trip
- Shows route details, transfer counts, and travel time
- Displays the journey on an interactive map
- Remembers recent searches and saves favorite routes

---

## 🚀 Quick start

### Local setup

```bash
git clone https://github.com/sejalpandey30/delhiRouteRecommender.git
cd delhiRouteRecommender
pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5050
```

The project includes a prebuilt network cache, so it runs immediately without rebuilding GTFS data.

---

## 📍 How to use

1. Enter an origin stop or station.
2. Enter a destination.
3. Pick a departure time.
4. Click the route button.
5. Review the trip, map, and transfer details.

---

## 🧠 Tech behind it

This project uses a RAPTOR-based routing engine for efficient multimodal planning.

- GTFS data is processed into a compact transit network
- Route patterns are grouped to reduce unnecessary computation
- Walking transfers are added between nearby stops
- The system reconstructs the best available journey

---

## 🏗️ Project structure

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

---

## ⚠️ Notes

- Walking transfers are estimated using straight-line distance, not full street-network routing.
- The planner uses static schedule data, not live transit disruptions.
- Fare calculation is not included yet.
- It currently optimizes for the fastest route.

---

## 🛠️ Future improvements

- Multi-criteria routing
- Real-time transit updates
- Better walking transfer models
- Day-of-week service filtering
- Fare integration

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a pull request

---

## 📚 References

- RAPTOR paper: https://research.microsoft.com/en-us/um/people/seidenbe/papers/raptor_alenex.pdf
- GTFS: https://gtfs.org/
- DMRC: https://delhimetrorail.com/
- DTC/DIMTS: https://www.dtc.nic.in/

---

## 📄 License

MIT License

---

## 👤 Author

Sejal Pandey
