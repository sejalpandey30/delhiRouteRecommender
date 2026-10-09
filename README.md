# 🚇 Delhi Transit — Multimodal Route Planner

**The fastest, most reliable way to navigate Delhi's public transportation network.**

A production-ready, open-source journey planner that seamlessly routes across Delhi's **Metro (DMRC)**, **Bus (DTC/DIMTS)**, and **walking transfers**. Powered by the industry-standard **RAPTOR algorithm** for optimal multimodal route planning.

**[🚀 Try it live →](https://delhi-route-recommender--sejalpandey30.replit.app)**

---

## ✨ Features

### 🎯 Smart Route Planning
- **Multimodal journeys**: Mix metro, bus, and walking in any combination
- **Optimized transfers**: Automatically finds the fastest route with fewest mode switches
- **Real-time visualization**: Interactive map showing your complete journey with color-coded legs
- **Departure time planning**: Plan your trip for any time of day

### 📚 Your Travel Data
- **Search history**: Keep track of your recent searches (up to 30)
- **Favorite routes**: Save frequently-used journeys for one-click planning
- **Journey details**: Total duration, transfer count, boarding/alighting times, and stop names

### 📍 Comprehensive Network Coverage
- **10,559 bus stops** across DTC/DIMTS network
- **263 metro stations** across DMRC lines (9 lines + Airport Express)
- **Automatic walking transfers** between nearby stops (up to 350m radius)
- Real DMRC line colors for easy visual identification

### ⚡ Fast & Lightweight
- **Sub-100ms queries** on prebuilt network cache
- **No external APIs needed** — entirely self-contained
- **Works offline** (once network cache is loaded)
- **Minimal dependencies** — pure Python with Flask backend

---

## 🚀 Quick Start

### Online (Recommended)
Visit **[delhi-route-recommender--sejalpandey30.replit.app](https://delhi-route-recommender--sejalpandey30.replit.app)** — no installation needed.

### Local Setup

**Requirements:** Python 3.8+

```bash
# Clone the repository
git clone https://github.com/sejalpandey30/delhiRouteRecommender.git
cd delhiRouteRecommender

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open **http://localhost:5050** in your browser.

The prebuilt network cache (`cache/network.pkl`) is included, so the app starts immediately—no GTFS data processing required.

---

## 📖 How to Use

### 1. **Search for Stops**
   - Type a **metro station name** or **bus stop name** in the search box
   - Use autocomplete to find your destination quickly
   - Stops are color-coded: 🔵 Metro | 🔴 Bus

### 2. **Set Departure Time**
   - Choose your desired departure time (default: 09:00)
   - The planner finds the fastest route available after that time

### 3. **Get Your Route**
   - Click **"Find Best Route"**
   - View the journey timeline with:
     - Each leg (transit or walking)
     - Mode, route, and line color
     - Departure and arrival times
     - Walking duration for transfers

### 4. **Save & Reuse**
   - **Save to favorites**: Click the ⭐ button to save your route
   - **View history**: Check your recent searches under "Recent Searches" tab

---

## 🏗️ Technical Architecture

### Backend Stack
- **Framework**: Flask 3.0+ (lightweight REST API)
- **Routing Engine**: Custom RAPTOR implementation (C-efficient via NumPy)
- **Data Storage**: SQLite (user history & favorites)
- **Network Cache**: Pickle-serialized data structures

### Frontend Stack
- **UI Framework**: Vanilla JavaScript + HTML5
- **Styling**: CSS3 (responsive design)
- **Mapping**: Leaflet.js + OpenStreetMap tiles
- **Autocomplete**: Client-side search with debouncing

### API Endpoints

#### Planning
- `GET /api/search?q=<query>` — Search for stops by name
- `GET /api/plan?origin=<idx>&dest=<idx>&time=<HH:MM>` — Get optimal route
- `GET /api/stops/<idx>` — Get lat/lon coordinates for a stop

#### History
- `GET /api/history` — Fetch recent searches (up to 30)
- `DELETE /api/history/<id>` — Delete a specific search
- `DELETE /api/history/clear` — Clear all history

#### Favorites
- `GET /api/favourites` — Fetch saved routes
- `POST /api/favourites` — Save a route with optional label
- `DELETE /api/favourites/<id>` — Remove a favorite

---

## 🧠 The RAPTOR Algorithm

This project implements **RAPTOR** (Round-based Public Transit Optimized Router), the same algorithm used by professional transit planners like OpenTripPlanner.

### Why RAPTOR?
| Traditional Approach | RAPTOR |
|---|---|
| One Dijkstra per trip (millions of edges) | One scan per route pattern per round |
| O(trips × stops × log stops) | O(rounds × patterns × stops) |
| Slow on large networks | **Fast even on 10K+ stops** |

### Algorithm Overview
1. **Patterns, not trips**: Groups trips with identical stop sequences (e.g., all "708 DOWN" runs). ~95K trips → ~2,400 patterns.
2. **Rounds as transit legs**: Round *k* finds earliest arrival using ≤ *k* transit legs.
3. **Walking transfers**: Computes ~4K footpath edges between stops within 350m (with 1.4× street detour factor).
4. **Convergence**: Stops when no improvement possible or max rounds reached.

**Result**: Multi-leg journeys (bus → metro → bus → walk) are found optimally in <100ms.

---

## 📊 Network Statistics

- **Total stops**: 10,822 (DTC: 10,559 bus + DMRC: 263 metro)
- **Route patterns**: ~2,400 (aggregating 95K+ individual trips)
- **Walking transfers**: ~4,000+ footpath edges
- **Network cache size**: ~100 MB (includes all GTFS data + routing structures)

---

## 🔧 Advanced: Updating GTFS Data

To rebuild the network with fresh GTFS feeds from DTC/DIMTS or DMRC:

### 1. Download Latest GTFS Feeds
- **DTC/DIMTS**: Download from official Delhi transit authority
- **DMRC**: Download from DMRC's open data portal

### 2. Extract and Structure
```
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

### 3. Rebuild Network Cache
```bash
python build_network.py
python app.py
```

### 4. Custom Paths (Optional)
```bash
export BUS_GTFS_DIR=/path/to/bus/gtfs
export METRO_GTFS_DIR=/path/to/metro/gtfs
export NETWORK_CACHE_PATH=/path/to/cache/network.pkl
python build_network.py
```

**This processes ~3.8M stop_time records and caches the result (~30s processing time).**

---

## ⚠️ Known Limitations

### Straight-line Walking Transfers
- Transfer distances are **Euclidean**, not street-network based
- A 350m transfer might be blocked by highway, river, or railway in reality
- **1.4× detour factor** is an approximation without OpenStreetMap data
- **Fix**: Integrate OSRM or Mapbox walking API (future enhancement)

### No Real-time Data
- Plans against **static published schedule only**
- No live delays, service disruptions, or vehicle locations
- **Fix**: Integrate real-time GTFS feeds from transit agencies (future)

### No Fare Calculation
- Optimizes for **arrival time only**, not ticket cost
- Fare rules in GTFS are skipped (large files, not essential for routing)
- **Fix**: Parse `fare_attributes.txt` + `fare_rules.txt` (future)

### Single-Criterion Optimization
- Returns **earliest arrival only**
- No "fewest transfers" or "least walking" alternatives
- **Fix**: Implement multi-criteria RAPTOR (Pareto frontier)

### Calendar/Service Not Filtered
- All trips treated as always-running (ignores `calendar.txt`)
- Weekday-only metro trips might appear on Sunday queries
- **Fix**: Add day-of-week filtering (future enhancement)

---

## 🎯 Roadmap & Future Improvements

- [ ] **Multi-criteria routing**: Offer alternatives (fewest transfers, least walking)
- [ ] **Real-time integration**: Live bus/metro locations & ETA adjustments
- [ ] **OSRM walking network**: Replace straight-line transfers
- [ ] **Service calendar filtering**: Respect day-of-week restrictions
- [ ] **Mobile app**: Native iOS/Android clients
- [ ] **Accessibility**: Wheelchair-accessible routes
- [ ] **Fare integration**: Real-time fare calculation
- [ ] **API rate-limiting**: For production deployments

---

## 🏃 Project Structure

```
.
├── app.py                    # Flask web server & REST API
├── raptor.py                 # RAPTOR routing algorithm + network loader
├── build_network.py          # GTFS processor → optimized cache
├── gtfs_loader.py            # GTFS CSV parser & normalizer
├── requirements.txt          # Python dependencies
├── cache/
│   └── network.pkl           # Prebuilt routing network (~100MB)
├── templates/
│   └── index.html            # Single-page frontend (HTML/CSS/JS)
├── data/
│   └── transit.db            # SQLite (user history & favorites)
└── README.md                 # This file
```

---

## 💡 Contributing

Found a bug? Have an idea? Contributions welcome!

1. **Fork** the repo
2. **Create** a feature branch (`git checkout -b feature/your-idea`)
3. **Commit** your changes (`git commit -m 'Add feature'`)
4. **Push** to branch (`git push origin feature/your-idea`)
5. **Open** a Pull Request

---

## 📚 References

- **RAPTOR Paper**: [Round-based Public Transit Optimized Router](https://research.microsoft.com/en-us/um/people/seidenbe/papers/raptor_alenex.pdf)
- **GTFS Spec**: [General Transit Feed Specification](https://gtfs.org/)
- **Delhi Metro**: [DMRC Official](https://delhimetrorail.com/)
- **Delhi Buses**: [DTC/DIMTS Official](https://www.dtc.nic.in/)

---

## 📄 License

MIT License — See [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Sejal Pandey** — Built with ❤️ for Delhi's transit commuters.

**Questions?** Open an issue on GitHub or reach out via [GitHub Issues](https://github.com/sejalpandey30/delhiRouteRecommender/issues).

---

**Last Updated**: October 2026  
**Status**: ✅ Production-ready | 📊 10K+ stops | ⚡ Sub-100ms queries
