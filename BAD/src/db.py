import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bad.db')

def get_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the required schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            result_type TEXT DEFAULT 'generic',
            file_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def add_result(job_id, file_url, result_type='generic'):
    """Adds a new result record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO results (job_id, result_type, file_url)
        VALUES (?, ?, ?)
    ''', (job_id, result_type, file_url))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_latest_result(job_id):
    """Retrieves the most recent result for a given job_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM results 
        WHERE job_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    ''', (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

if __name__ == "__main__":
    init_db()
