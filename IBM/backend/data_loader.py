# backend/data_loader.py
import pandas as pd
import sqlite3
from datetime import datetime
import os
import time
import googlemaps

# Import db_config for database interaction and config for the API Key
from db_config import init_db, get_db_connection, DATABASE_NAME
import config

# Path for the local CSV file that contains the hospital data
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), 'hospital_data_raw.csv')

# --- GOOGLE MAPS PLATFORM CONFIGURATION ---
# Initialize Google Maps client from the config file using the correct variable name
try:
    gmaps_client = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)
    print("Google Maps client initialized successfully.")
except Exception as e:
    gmaps_client = None
    print(f"WARNING: Could not initialize Google Maps client: {e}")
    print("Geocoding will be skipped.")

# Add a small delay between API calls to respect rate limits
GEOCODING_DELAY = 0.1 # Seconds

def geocode_address(address):
    """
    Geocodes an address using the Google Maps Platform Geocoding API.
    """
    if gmaps_client is None:
        print(f"  Geocoding client not initialized. Cannot geocode: {address}")
        return None, None

    print(f"Attempting to geocode: {address}")
    try:
        geocode_result = gmaps_client.geocode(address)
        if geocode_result:
            lat = geocode_result[0]['geometry']['location']['lat']
            lon = geocode_result[0]['geometry']['location']['lng']
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print(f"  Error geocoding '{address}': {e}")
        return None, None

def load_static_hospital_data():
    """
    Loads hospital data from a local CSV file, cleans it, geocodes it,
    and loads it into the SQLite database.
    """
    print("--- Starting static data load process ---")
    
    try:
        hospital_data_df = pd.read_csv(CSV_FILE_PATH)
        print(f"Successfully loaded {len(hospital_data_df)} rows from CSV: {CSV_FILE_PATH}")
    except FileNotFoundError:
        print(f"ERROR: No CSV file found at {CSV_FILE_PATH}. Please ensure 'hospital_data_raw.csv' is in the 'backend' folder.")
        return
    except Exception as e:
        print(f"ERROR: Failed to load from CSV: {e}")
        return

    # --- Data Cleaning ---
    print("Cleaning data...")
    hospital_data_df.columns = hospital_data_df.columns.str.strip().str.lower()

    if 'hospital_name' not in hospital_data_df.columns:
        print("ERROR: CSV file must contain a 'hospital_name' column.")
        return

    hospital_data_df['hospital_id'] = hospital_data_df['hospital_name'].apply(
        lambda x: str(x).strip().lower().replace(' ', '_').replace('.', '')
    )
    hospital_data_df['full_address'] = hospital_data_df['hospital_name'].apply(
        lambda x: str(x).strip() + ", Delhi, India"
    )
    hospital_data_df['last_scrape_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # --- Geocode and Populate DB ---
    print("Connecting to database and populating hospitals table...")
    conn = get_db_connection()
    cursor = conn.cursor()

    for index, row in hospital_data_df.iterrows():
        latitude, longitude = geocode_address(row['full_address'])
        time.sleep(GEOCODING_DELAY) 
        
        data_to_insert = (
            row.get('hospital_id', ''),
            row.get('hospital_name', ''),
            row.get('full_address', ''),
            latitude,
            longitude,
            row.get('total_free_bed', 0),
            row.get('total_free_critical_bed_wo_vent', 0),
            row.get('total_free_critical_bed_with_vent', 0),
            row.get('total_free_non_critical_bed', 0),
            row.get('available_free_critical_bed_wo_vent', 0),
            row.get('available_free_critical_bed_with_vent', 0),
            row.get('available_free_non_critical_bed', 0),
            row.get('last_scrape_date', ''),
            row.get('estimated_wait_time_mins', 30)
        )

        cursor.execute('''
            INSERT OR REPLACE INTO hospitals (
                hospital_id, hospital_name, full_address, latitude, longitude,
                total_free_bed, total_free_critical_bed_wo_vent, total_free_critical_bed_with_vent,
                total_free_non_critical_bed, available_free_critical_bed_wo_vent,
                available_free_critical_bed_with_vent, available_free_non_critical_bed, 
                last_scrape_date, estimated_wait_time_mins
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data_to_insert)
        
    conn.commit()
    conn.close()
    print(f"Successfully loaded/updated {len(hospital_data_df)} hospitals into '{DATABASE_NAME}'.")
    print("--- Static data load process complete ---")

# --- How to run this script ---
if __name__ == '__main__':
    # Initialize the database (creates the .db file and table if they don't exist)
    init_db()

    # Load the static data
    load_static_hospital_data()

    print("\nData loading script finished.")
    print(f"Your static hospital data is now in '{DATABASE_NAME}'.")
