# backend/db_config.py
import sqlite3
import os

# CHANGED DATABASE NAME HERE:
DATABASE_NAME = 'hospital_data.db'
# Define DB_PATH relative to the directory where this script is located
DB_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

# db_config.py

# db_config.py

# db_config.py

def init_db():
    """Initializes the SQLite database and creates the hospitals table."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # This schema MUST include the new wait time column at the end
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id TEXT PRIMARY KEY,
            hospital_name TEXT NOT NULL,
            full_address TEXT,
            latitude REAL,
            longitude REAL,
            total_free_bed INTEGER,
            total_free_critical_bed_wo_vent INTEGER,
            total_free_critical_bed_with_vent INTEGER,
            total_free_non_critical_bed INTEGER,
            available_free_critical_bed_wo_vent INTEGER,
            available_free_critical_bed_with_vent INTEGER,
            available_free_non_critical_bed INTEGER,
            last_scrape_date TEXT,
            estimated_wait_time_mins INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    
    print(f"Database '{DATABASE_NAME}' initialized and 'hospitals' table created/checked at: {DB_PATH}")

if __name__ == '__main__':
    # This block allows you to run this file directly to initialize the DB
    # Example: python backend/db_config.py
    init_db()
