# app.py

# --- Imports ---
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import config
import googlemaps

# --- Flask Application Initialization ---
app = Flask(__name__)
CORS(app)

# --- Google Maps Client Initialization ---
# ✅ CORRECTED THIS LINE
gmaps = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)

# --- Database Connection Function ---
def get_db_connection():
    conn = sqlite3.connect(config.DATABASE_URI)
    conn.row_factory = sqlite3.Row
    return conn

# --- Home Route (Basic Test) ---
@app.route('/')
def home():
    return "Ambulance Routing API is running!"


# app.py

# app.py

@app.route('/api/search_hospitals', methods=['POST'])
def search_hospitals():
    conn = get_db_connection()
    db_hospitals = conn.execute("SELECT * FROM hospitals").fetchall()
    conn.close()

    found_hospitals = []
    for row in db_hospitals:
        hospital = dict(row)
        
        if hospital.get('latitude') and hospital.get('longitude'):
            bed_details = {
                "total": hospital.get('total_free_bed', 0),
                "critical_vent": hospital.get('available_free_critical_bed_with_vent', 0),
                "critical_no_vent": hospital.get('available_free_critical_bed_wo_vent', 0),
                "non_critical": hospital.get('available_free_non_critical_bed', 0)
            }

            hospital_info = {
                "name": hospital.get('hospital_name'),
                "latitude": hospital.get('latitude'),
                "longitude": hospital.get('longitude'),
                "address": hospital.get('full_address'),
                "bed_availability": bed_details,
                # Get the wait time from the database
                "estimated_wait_time": hospital.get('estimated_wait_time_mins', 30)
            }
            found_hospitals.append(hospital_info)

    return jsonify(found_hospitals)

# --- API Endpoint: /api/select_optimal_hospital ---
@app.route('/api/select_optimal_hospital', methods=['POST'])
def select_optimal_hospital():
    data = request.get_json()
    patient_lat = data.get('patient_latitude')
    patient_lon = data.get('patient_longitude')
    patient_threat_level = data.get('patient_threat_level')
    hospitals = data.get('hospitals')

    if not all([patient_lat, patient_lon, patient_threat_level, hospitals]):
        return jsonify({"error": "Missing required data"}), 400

    optimal_hospital = None
    best_score = -1

    WEIGHTS = {
        "threat_level": 0.4,
        "bed_availability": 0.1,
        "wait_time": 0.2,
        "travel_time": 0.3
    }

    origins = [(patient_lat, patient_lon)]
    destinations = [(h['latitude'], h['longitude']) for h in hospitals]
    travel_times = {}

    if destinations:
        try:
            matrix_results = gmaps.distance_matrix(origins, destinations, mode="driving", traffic_model="best_guess", departure_time="now")
            if matrix_results['status'] == 'OK':
                for j, element in enumerate(matrix_results['rows'][0]['elements']):
                    if element['status'] == 'OK':
                        target_lat, target_lon = destinations[j]
                        travel_times[f"{target_lat},{target_lon}"] = element['duration']['value']
                    else:
                        target_lat, target_lon = destinations[j]
                        travel_times[f"{target_lat},{target_lon}"] = 999999
        except Exception as e:
            print(f"Error fetching Google Distance Matrix: {e}")

    for hospital in hospitals:
        h_key = f"{hospital['latitude']},{hospital['longitude']}"
        travel_duration_seconds = travel_times.get(h_key, 999999)
        
        normalized_threat = patient_threat_level / 5.0
        normalized_beds = hospital['bed_availability'] / 50.0
        normalized_wait_time = (300 - min(hospital['estimated_wait_time'], 300)) / 300.0
        normalized_travel_time = (3600 - min(travel_duration_seconds, 3600)) / 3600.0

        current_score = (WEIGHTS["threat_level"] * normalized_threat) + \
                        (WEIGHTS["bed_availability"] * normalized_beds) + \
                        (WEIGHTS["wait_time"] * normalized_wait_time) + \
                        (WEIGHTS["travel_time"] * normalized_travel_time)

        hospital['calculated_score'] = current_score
        if current_score > best_score:
            best_score = current_score
            optimal_hospital = hospital

    if optimal_hospital:
        return jsonify(optimal_hospital)
    else:
        return jsonify({"message": "No optimal hospital found"}), 404

# --- API Endpoint: /api/get_route ---
@app.route('/api/get_route', methods=['POST'])
def get_route():
    data = request.get_json()
    origin = (data.get('ambulance_latitude'), data.get('ambulance_longitude'))
    destination = (data.get('hospital_latitude'), data.get('hospital_longitude'))

    if not all(origin) or not all(destination):
        return jsonify({"error": "Missing required location data"}), 400

    try:
        directions_result = gmaps.directions(origin, destination, mode="driving", departure_time="now")
        if directions_result:
            return jsonify(directions_result[0])
        else:
            return jsonify({"message": "No route found"}), 404
    except Exception as e:
        return jsonify({"error": f"Google Directions API error: {str(e)}"}), 500

# --- Main Execution Block ---
if __name__ == '__main__':
    app.run(debug=True)
