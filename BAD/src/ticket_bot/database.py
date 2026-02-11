import sqlite3
import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="tickets.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the tickets table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tickets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                channel_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
                helper_id INTEGER,
                status TEXT DEFAULT 'open',
                issue_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_ticket(self, ticket_id, channel_id, user_id, user_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO tickets (ticket_id, channel_id, user_id, user_name, status)
                VALUES (?, ?, ?, ?, 'setup')
            ''', (ticket_id, channel_id, user_id, user_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def update_ticket_status(self, channel_id, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tickets SET status = ? WHERE channel_id = ?
        ''', (status, channel_id))
        conn.commit()
        conn.close()

    def assign_helper(self, channel_id, helper_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tickets SET helper_id = ? WHERE channel_id = ?
        ''', (helper_id, channel_id))
        conn.commit()
        conn.close()

    def get_ticket_by_channel(self, channel_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tickets WHERE channel_id = ?', (channel_id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def close_ticket(self, channel_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tickets 
            SET status = 'closed', closed_at = ? 
            WHERE channel_id = ?
        ''', (datetime.datetime.now(), channel_id))
        conn.commit()
        conn.close()

    def delete_ticket(self, channel_id):
        """Removes the ticket record completely."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tickets WHERE channel_id = ?', (channel_id,))
        conn.commit()
        conn.close()
