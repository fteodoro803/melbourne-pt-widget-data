from database import get_data_version, get_routes, is_db_connected, get_shapes, get_trips, get_route_shapes
from data_processing import update_gtfs_data
from datetime import datetime
from cloud import upload_file_to_cloud_storage
from flask import Flask, jsonify, request


# Flask instance
app = Flask(__name__)

@app.route("/update", methods=["POST"])
def update():
    """Update GTFS data endpoint."""
    try:
        start: datetime = datetime.now()
        was_updated = update_gtfs_data()

        if was_updated:
            # Use the helper function for uploads if needed
            # upload_file_to_cloud_storage(VERSION_FILE)

            total_time = (datetime.now() - start).seconds
            return jsonify({
                "message": f"Finished updating data, took {total_time} seconds",
                "updated": True,
            }), 200
        else:
            return jsonify({
                "message": "No update needed",
                "updated": False,
            }), 200

    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {str(e)}\n", 500


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    db_connected: bool = is_db_connected()

    if not db_connected:
        return jsonify({
            "status": "unhealthy",
            "reason": "MongoDB connection not working",
        }), 503

    return jsonify({
        "status": "ok"
    }), 200

@app.route("/version", methods=["GET"])
def version():
    """Gets the current version date of saved GTFS Schedule data."""
    data_version: datetime = get_data_version()

    return jsonify({
        "version": data_version
    }), 200

@app.route("/routes", methods=["GET"])
def routes():
    """Gets all tram routes offered by PTV in GTFS format."""
    route_type: str|None = request.args.get("type")

    if route_type:
        route_type = route_type.lower()     # normalisation
        allowed_route_types = ["tram", "train", "bus"]

        # Checks if inputted route type contains a word of the transport options
        if not route_type in allowed_route_types:
            return jsonify({
                "status": "bad request",
                "reason": f"{route_type} is not a valid type. Valid types are: {', '.join(allowed_route_types)}."
            }), 400

    gtfs_routes = get_routes(route_type)
    return jsonify(gtfs_routes), 200

@app.route("/shapes", methods=["GET"])
def shapes():
    """Gets all shapes/geo-paths for a specified shape_id."""
    shape_id = request.args.get("id")
    gtfs_shapes = get_shapes(shape_id)
    return jsonify(gtfs_shapes), 200

@app.route("/routeShapes", methods=["GET"])
def routeShapes():
    """Gets all shapes for a specified route_id."""
    route_id = request.args.get("id")
    shape_ids = get_route_shapes(route_id)

    # Accumulate all shapes data for each shape id
    gtfs_shapes = []
    for shape in shape_ids:
        shape_data = get_shapes(shape)
        gtfs_shapes.extend(shape_data)

    return jsonify(gtfs_shapes)

@app.route("/trips", methods=["GET"])
def trips():
    """Gets all trips for a specified route_id."""
    route_id = request.args.get("id")
    gtfs_trips = get_trips(route_id)
    return jsonify(gtfs_trips), 200

# For local testing Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
