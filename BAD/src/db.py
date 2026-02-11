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

    # Create tickets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT,
            guild_id TEXT,
            user_id TEXT,
            user_name TEXT,
            status TEXT DEFAULT 'draft',
            title TEXT,
            description TEXT,
            urgency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
    ''')
    # Index for fast lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_channel_id ON tickets(channel_id)')

    # Migration: Check if archive_path exists
    try:
        cursor.execute("SELECT archive_path FROM tickets LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️ Migrating Database: Adding archive_path to tickets table...")
        try:
             cursor.execute("ALTER TABLE tickets ADD COLUMN archive_path TEXT")
        except Exception as e:
             print(f"❌ Migration failed: {e}")

    # Migration: Check if assigned_to exists
    try:
        cursor.execute("SELECT assigned_to FROM tickets LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️ Migrating Database: Adding assigned_to to tickets table...")
        try:
             cursor.execute("ALTER TABLE tickets ADD COLUMN assigned_to TEXT")
        except Exception as e:
             print(f"❌ Migration failed: {e}")

    conn.commit()
    conn.close()

def create_ticket_record(channel_id, guild_id, user_id, user_name):
    """Creates a new ticket record and returns the ticket ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tickets (channel_id, guild_id, user_id, user_name, status)
        VALUES (?, ?, ?, ?, 'draft')
    ''', (str(channel_id), str(guild_id), str(user_id), user_name))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

def update_ticket_details(channel_id, title, description, urgency):
    """Updates ticket details (usually from draft)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets 
        SET title = ?, description = ?, urgency = ?
        WHERE channel_id = ?
    ''', (title, description, urgency, str(channel_id)))
    conn.commit()
    conn.close()

def update_ticket_status(channel_id, status):
    """Updates the status of a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status == 'closed':
        cursor.execute('''
            UPDATE tickets 
            SET status = ?, closed_at = CURRENT_TIMESTAMP
            WHERE channel_id = ?
        ''', (status, str(channel_id)))
    else:
        cursor.execute('''
            UPDATE tickets 
            SET status = ?
            WHERE channel_id = ?
        ''', (status, str(channel_id)))
        
    conn.commit()
    conn.close()

def get_ticket(channel_id):
    """Retrieves ticket data by channel ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE channel_id = ?', (str(channel_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def update_ticket_assignment(channel_id, user_id):
    """Updates the assigned user for a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets 
        SET assigned_to = ?
        WHERE channel_id = ?
    ''', (str(user_id) if user_id else None, str(channel_id)))
    conn.commit()
    conn.close()

def get_ticket_status(channel_id):
    """Retrieves the status of a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM tickets WHERE channel_id = ?', (str(channel_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_closed_tickets():
    """Retrieves all closed tickets ordered by closed_at descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tickets 
        WHERE status = 'closed'
        ORDER BY closed_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_ticket_archived(channel_id):
    """Updates the status of a ticket to 'archived'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets 
        SET status = 'archived'
        WHERE channel_id = ?
    ''', (str(channel_id),))
    conn.commit()
    conn.close()

def update_archive_path(channel_id, path):
    """Updates the archive path for a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets 
        SET archive_path = ?
        WHERE channel_id = ?
    ''', (path, str(channel_id)))
    conn.commit()
    conn.close()

def get_archive_path(ticket_id):
    """Retrieves the archive path by ticket ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT archive_path FROM tickets WHERE id = ?', (str(ticket_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_user_tickets(user_id):
    """Retrieves all tickets for a specific user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tickets 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (str(user_id),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_ticket_by_id(ticket_id):
    """Retrieves ticket data by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE id = ?', (str(ticket_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_ticket_stats():
    """Returns statistics for tickets."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {
        "total_open": 0,
        "unassigned": 0,
        "urgent": 0,
        "active_list": []
    }
    
    # Get Counts
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'active'")
    stats['total_open'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'active' AND (assigned_to IS NULL OR assigned_to = '')")
    stats['unassigned'] = cursor.fetchone()[0]
    
    # Urgency check (loose string match)
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'active' AND (urgency LIKE '%High%' OR urgency LIKE '%10%' OR urgency LIKE '%9%' OR urgency LIKE '%Urgent%')")
    stats['urgent'] = cursor.fetchone()[0]
    
    # Get Active List
    cursor.execute("SELECT * FROM tickets WHERE status = 'active' ORDER BY created_at DESC")
    stats['active_list'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return stats

def get_unassigned_tickets(limit=5):
    """Retrieves unassigned active tickets, prioritizing urgency."""
    conn = get_connection()
    cursor = conn.cursor()
    # Sort by urgency (descending string sort isn't perfect but 'High' > 'Low' alphabetically? No. 
    # Logic: urgency is text. We should probably sort by created_at for FIFO or implement urgency weights.
    # Current system uses text: "10 - Critical", "Medium", etc.
    # Let's just sort by created_at ASC (Oldest first) for fairness, or maybe filtered by urgency keyword?
    # Simple approach: Oldest unassigned first.
    cursor.execute('''
        SELECT * FROM tickets 
        WHERE status = 'active' AND (assigned_to IS NULL OR assigned_to = '')
        ORDER BY created_at ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_assigned_tickets(user_id):
    """Retrieves active tickets assigned to a specific user (Helper View)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM tickets 
        WHERE status = 'active' AND assigned_to = ?
        ORDER BY created_at DESC
    ''', (str(user_id),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_active_tickets():
     stats = get_ticket_stats()
     return stats['active_list']

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

def get_tickets_with_filter(status=None, user_id=None, limit=10, offset=0, sort_desc=True, search_query=None, urgency=None):
    """Retrieves tickets with filtering and pagination."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if status:
        if isinstance(status, list):
            placeholders = ','.join(['?'] * len(status))
            query += f" AND status IN ({placeholders})"
            params.extend(status)
        else:
            query += " AND status = ?"
            params.append(status)
            
    if user_id:
        query += " AND user_id = ?"
        params.append(str(user_id))

    if search_query:
        # Search in title, user_name, or description
        query += " AND (title LIKE ? OR user_name LIKE ? OR description LIKE ?)"
        wildcard_query = f"%{search_query}%"
        params.extend([wildcard_query, wildcard_query, wildcard_query])

    if urgency:
        # Strict or partial match? Let's do partial for flexibility since it's text
        query += " AND urgency LIKE ?"
        params.append(f"%{urgency}%")
        
    order = "DESC" if sort_desc else "ASC"
    query += f" ORDER BY created_at {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) FROM tickets WHERE 1=1"
    count_params = []
    
    if status:
        if isinstance(status, list):
             placeholders = ','.join(['?'] * len(status))
             count_query += f" AND status IN ({placeholders})"
             count_params.extend(status)
        else:
            count_query += " AND status = ?"
            count_params.append(status)
            
    if user_id:
        count_query += " AND user_id = ?"
        count_params.append(str(user_id))
        
    if search_query:
        count_query += " AND (title LIKE ? OR user_name LIKE ? OR description LIKE ?)"
        wildcard_query = f"%{search_query}%"
        count_params.extend([wildcard_query, wildcard_query, wildcard_query])

    if urgency:
        count_query += " AND urgency LIKE ?"
        count_params.append(f"%{urgency}%")
        
    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]
    
    conn.close()
    return [dict(row) for row in rows], total_count

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

def delete_conversation(conversation_id):
    """Deletes a conversation and its messages."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Enable foreign key support just in case, though we'll delete manually to be safe
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Delete messages first
    cursor.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    
    # Delete conversation
    cursor.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
    
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
