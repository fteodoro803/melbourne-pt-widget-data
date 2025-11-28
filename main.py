from datetime import datetime
from data_processing import update_gtfs_data
from cloud import upload_file_to_cloud_storage
from flask import Flask, jsonify

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
                "updated": True
            }), 200
        else:
            return 'No update needed\n', 200

    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {str(e)}\n", 500


@app.route("/health", methods=["POST"])
def health():
    """Health check."""
    return jsonify("Health check succeeded"), 200


# For local testing
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
