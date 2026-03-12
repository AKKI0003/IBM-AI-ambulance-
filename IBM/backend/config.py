# config.py
import os

# ✅ Use a real Google Maps API Key or fallback to the default (replace with a secure method in production)
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyC_T6tfk_05jELHSy6iRXd5eQ7RfoXVJM8")

# ✅ Correct path to SQLite database (same as db_config.py)
DATABASE_URI = os.path.join(os.path.dirname(__file__), 'hospital_data.db')
