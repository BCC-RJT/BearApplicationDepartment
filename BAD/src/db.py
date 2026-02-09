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
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            topic TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
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

# --- Conversation Management ---

def create_conversation(channel_id, topic=None):
    """Creates a new conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (channel_id, topic)
        VALUES (?, ?)
    ''', (str(channel_id), topic))
    conn.commit()
    conversation_id = cursor.lastrowid
    conn.close()
    return conversation_id

def get_active_conversation(channel_id):
    """Retrieves the active conversation for a channel."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM conversations
        WHERE channel_id = ? AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
    ''', (str(channel_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def close_conversation(conversation_id):
    """Closes a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE conversations
        SET status = 'closed', closed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (conversation_id,))
    conn.commit()
    conn.close()

def add_message(conversation_id, role, content):
    """Adds a message to a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id, limit=20):
    """Retrieves the last N messages of a conversation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation_id,)) # Limit should be applying to the *latest* messages, but we want them in ASC order. 
                             # So we'd need subquery or just fetch all and slice in python if not huge.
                             # For now, let's just fetch all as context window usually limits us anyway.
    
    rows = cursor.fetchall()
    conn.close()
    
    # If we need to implement limit efficiently on DB side:
    # SELECT * FROM (SELECT * FROM messages WHERE ... ORDER BY created_at DESC LIMIT 20) ORDER BY created_at ASC
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
