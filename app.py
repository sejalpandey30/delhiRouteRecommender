"""
Flask web app exposing the RAPTOR multimodal journey planner over the
Delhi bus + metro network as a searchable, interactive platform.
"""
from flask import Flask, request, jsonify, render_template
from raptor import Network, RaptorRouter, fmt_time

app = Flask(__name__)

# Real DMRC line colors, keyed by the color word GTFS embeds at the start
# of route_long_name (e.g. "YELLOW_Samaypur Badli to Huda City Centre").
METRO_LINE_COLORS = {
    "YELLOW": "#FFC300",
    "RED": "#E4232A",
    "BLUE": "#0072BC",
    "VIOLET": "#7B2D8E",
    "PINK": "#EC008C",
    "MAGENTA": "#97144D",
    "GREEN": "#00A651",
    "ORANGE/AIRPORT": "#F7941D",
    "AQUA": "#00AEEF",
    "GRAY": "#8A8D8F",
    "RAPID": "#B08D57",
}
BUS_COLOR = "#C8443C"
WALK_COLOR = "#9AA0A6"


def leg_color(mode, route_long_name):
    if mode == "bus":
        return BUS_COLOR
    word = (route_long_name or "").split("_", 1)[0].upper()
    return METRO_LINE_COLORS.get(word, "#555555")


print("Loading network...")
net = Network()
router = RaptorRouter(net)
print("Ready:", net.n_stops, "stops")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    results = net.search_stops(q, limit=12)
    return jsonify(results)


@app.route("/api/plan")
def api_plan():
    try:
        origin_idx = int(request.args["origin"])
        dest_idx = int(request.args["dest"])
    except (KeyError, ValueError):
        return jsonify({"error": "origin and dest stop indices required"}), 400

    time_str = request.args.get("time", "09:00")
    try:
        h, m = map(int, time_str.split(":"))
        dep_sec = h * 3600 + m * 60
    except Exception:
        return jsonify({"error": "time must be HH:MM"}), 400

    if origin_idx == dest_idx:
        return jsonify({"error": "Origin and destination are the same stop"}), 400

    result = router.plan(origin_idx, dest_idx, dep_sec)
    if result is None:
        return jsonify({"error": "No route found within the search window"}), 404

    origin_name = net.stop_names[origin_idx]
    dest_name = net.stop_names[dest_idx]

    legs_out = []
    for leg in result["legs"]:
        if leg["type"] == "transit":
            line_name = leg["route_long_name"].split("_", 1)[-1] if "_" in leg["route_long_name"] else leg["route_long_name"]
            legs_out.append({
                "type": "transit",
                "mode": leg["mode"],
                "route": leg["route_short_name"] or leg["route_long_name"],
                "line_name": line_name,
                "color": leg_color(leg["mode"], leg["route_long_name"]),
                "board_stop": leg["board_stop"],
                "board_time": fmt_time(leg["board_time"]),
                "alight_stop": leg["alight_stop"],
                "alight_time": fmt_time(leg["alight_time"]),
            })
        else:
            legs_out.append({
                "type": "walk",
                "from_stop": leg["from_stop"],
                "to_stop": leg["to_stop"],
                "walk_minutes": max(1, round(leg["walk_seconds"] / 60)),
            })

    total_min = round((result["arrival_time"] - dep_sec) / 60)
    n_transfers = max(0, len([l for l in legs_out if l["type"] == "transit"]) - 1)

    return jsonify({
        "origin": origin_name,
        "destination": dest_name,
        "departure_time": fmt_time(dep_sec),
        "arrival_time": fmt_time(result["arrival_time"]),
        "duration_minutes": total_min,
        "transfers": n_transfers,
        "legs": legs_out,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
