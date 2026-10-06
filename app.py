"""
Flask web app — Delhi multimodal transit planner (RAPTOR).
New in v2:
  - SQLite database for search history & favourite routes
  - /api/history  GET / DELETE
  - /api/favourites  GET / POST / DELETE
  - /api/stops/<idx>  returns lat/lon for map marker placement
  - /api/plan now persists each successful plan to history
"""
from flask import Flask, request, jsonify, render_template, g
from raptor import Network, RaptorRouter, fmt_time
import sqlite3, os, json, time

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "transit.db")

# ── Metro line colours ────────────────────────────────────────────────────────
METRO_LINE_COLORS = {
    "YELLOW": "#FFC300", "RED": "#E4232A", "BLUE": "#0072BC",
    "VIOLET": "#7B2D8E", "PINK": "#EC008C", "MAGENTA": "#97144D",
    "GREEN": "#00A651", "ORANGE/AIRPORT": "#F7941D",
    "AQUA": "#00AEEF", "GRAY": "#8A8D8F", "RAPID": "#B08D57",
}
BUS_COLOR  = "#C8443C"
WALK_COLOR = "#9AA0A6"


def leg_color(mode, route_long_name):
    if mode == "bus":
        return BUS_COLOR
    word = (route_long_name or "").split("_", 1)[0].upper()
    return METRO_LINE_COLORS.get(word, "#555555")


# ── Network (loaded once at startup) ─────────────────────────────────────────
print("Loading network …")
net    = Network()
router = RaptorRouter(net)
print(f"Ready: {net.n_stops} stops")


# ── Database helpers ──────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_idx    INTEGER NOT NULL,
            origin_name   TEXT    NOT NULL,
            dest_idx      INTEGER NOT NULL,
            dest_name     TEXT    NOT NULL,
            depart_time   TEXT    NOT NULL,
            duration_min  INTEGER,
            transfers     INTEGER,
            searched_at   INTEGER NOT NULL   -- unix timestamp
        );

        CREATE TABLE IF NOT EXISTS favourites (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_idx  INTEGER NOT NULL,
            origin_name TEXT    NOT NULL,
            dest_idx    INTEGER NOT NULL,
            dest_name   TEXT    NOT NULL,
            label       TEXT    DEFAULT '',
            added_at    INTEGER NOT NULL,
            UNIQUE(origin_idx, dest_idx)
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    results = net.search_stops(q, limit=12)
    return jsonify(results)


@app.route("/api/stops/<int:idx>")
def api_stop(idx):
    """Return lat/lon of a single stop (used by map)."""
    if idx < 0 or idx >= net.n_stops:
        return jsonify({"error": "stop not found"}), 404
    return jsonify({
        "stop_idx":  idx,
        "name":      net.stop_names[idx],
        "mode":      net.stop_modes[idx],
        "lat":       float(net.stop_lats[idx]),
        "lon":       float(net.stop_lons[idx]),
    })


@app.route("/api/plan")
def api_plan():
    try:
        origin_idx = int(request.args["origin"])
        dest_idx   = int(request.args["dest"])
    except (KeyError, ValueError):
        return jsonify({"error": "origin and dest stop indices required"}), 400

    time_str = request.args.get("time", "09:00")
    try:
        h, m   = map(int, time_str.split(":"))
        dep_sec = h * 3600 + m * 60
    except Exception:
        return jsonify({"error": "time must be HH:MM"}), 400

    if origin_idx == dest_idx:
        return jsonify({"error": "Origin and destination are the same stop"}), 400

    result = router.plan(origin_idx, dest_idx, dep_sec)
    if result is None:
        return jsonify({"error": "No route found within the search window"}), 404

    origin_name = net.stop_names[origin_idx]
    dest_name   = net.stop_names[dest_idx]

    legs_out = []
    stop_coords = []   # list of {name, lat, lon} in journey order for the map

    # origin marker
    stop_coords.append({
        "name": origin_name, "mode": net.stop_modes[origin_idx],
        "lat": float(net.stop_lats[origin_idx]),
        "lon": float(net.stop_lons[origin_idx]),
    })

    for leg in result["legs"]:
        if leg["type"] == "transit":
            line_name = (
                leg["route_long_name"].split("_", 1)[-1]
                if "_" in leg["route_long_name"]
                else leg["route_long_name"]
            )
            color = leg_color(leg["mode"], leg["route_long_name"])
            legs_out.append({
                "type":       "transit",
                "mode":       leg["mode"],
                "route":      leg["route_short_name"] or leg["route_long_name"],
                "line_name":  line_name,
                "color":      color,
                "board_stop": leg["board_stop"],
                "board_time": fmt_time(leg["board_time"]),
                "alight_stop":leg["alight_stop"],
                "alight_time":fmt_time(leg["alight_time"]),
            })
            # alight stop coords for map
            alight_idx = net.stop_id_to_idx.get(
                next((sid for sid, n in zip(net.stop_ids, net.stop_names)
                      if n == leg["alight_stop"]), None), None)
            # fallback: just push dest coords at end; precise per-stop below
        else:
            legs_out.append({
                "type":         "walk",
                "from_stop":    leg["from_stop"],
                "to_stop":      leg["to_stop"],
                "walk_minutes": max(1, round(leg["walk_seconds"] / 60)),
            })

    # Build ordered stop coordinate list from stop names in legs
    seen = {origin_name}
    for leg in legs_out:
        names = []
        if leg["type"] == "transit":
            names = [leg["board_stop"], leg["alight_stop"]]
        else:
            names = [leg["from_stop"], leg["to_stop"]]
        for nm in names:
            if nm not in seen:
                seen.add(nm)
                # find first matching stop index by name
                for i, sn in enumerate(net.stop_names):
                    if sn == nm:
                        stop_coords.append({
                            "name": nm,
                            "mode": net.stop_modes[i],
                            "lat":  float(net.stop_lats[i]),
                            "lon":  float(net.stop_lons[i]),
                        })
                        break

    total_min  = round((result["arrival_time"] - dep_sec) / 60)
    n_transfers = max(0, len([l for l in legs_out if l["type"] == "transit"]) - 1)

    # ── Persist to history ────────────────────────────────────────────────────
    try:
        db = get_db()
        db.execute(
            """INSERT INTO history
               (origin_idx, origin_name, dest_idx, dest_name,
                depart_time, duration_min, transfers, searched_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (origin_idx, origin_name, dest_idx, dest_name,
             time_str, total_min, n_transfers, int(time.time()))
        )
        db.commit()
    except Exception:
        pass  # never let DB errors break the plan response

    return jsonify({
        "origin":           origin_name,
        "destination":      dest_name,
        "departure_time":   fmt_time(dep_sec),
        "arrival_time":     fmt_time(result["arrival_time"]),
        "duration_minutes": total_min,
        "transfers":        n_transfers,
        "legs":             legs_out,
        "stop_coords":      stop_coords,   # for Leaflet map
    })


# ── History endpoints ─────────────────────────────────────────────────────────
@app.route("/api/history")
def api_history():
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM history ORDER BY searched_at DESC LIMIT 30"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/history/<int:hid>", methods=["DELETE"])
def api_history_delete(hid):
    db = get_db()
    db.execute("DELETE FROM history WHERE id=?", (hid,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/history/clear", methods=["DELETE"])
def api_history_clear():
    db = get_db()
    db.execute("DELETE FROM history")
    db.commit()
    return jsonify({"ok": True})


# ── Favourites endpoints ──────────────────────────────────────────────────────
@app.route("/api/favourites", methods=["GET"])
def api_favs_get():
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM favourites ORDER BY added_at DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/favourites", methods=["POST"])
def api_favs_add():
    body = request.get_json(force=True)
    try:
        origin_idx  = int(body["origin_idx"])
        dest_idx    = int(body["dest_idx"])
        origin_name = net.stop_names[origin_idx]
        dest_name   = net.stop_names[dest_idx]
        label       = body.get("label", "")
    except (KeyError, ValueError, IndexError):
        return jsonify({"error": "origin_idx and dest_idx required"}), 400

    db = get_db()
    try:
        db.execute(
            """INSERT OR IGNORE INTO favourites
               (origin_idx, origin_name, dest_idx, dest_name, label, added_at)
               VALUES (?,?,?,?,?,?)""",
            (origin_idx, origin_name, dest_idx, dest_name, label, int(time.time()))
        )
        db.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


@app.route("/api/favourites/<int:fid>", methods=["DELETE"])
def api_favs_delete(fid):
    db = get_db()
    db.execute("DELETE FROM favourites WHERE id=?", (fid,))
    db.commit()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
