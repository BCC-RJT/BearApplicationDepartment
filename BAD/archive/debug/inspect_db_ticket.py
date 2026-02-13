
import sqlite3

db_path = "data/bad.db"

def inspect_db():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Searching for ticket with ID 21 in tickets table...")
        # Columns: id, channel_id, guild_id, user_id, user_name, status, title, description, urgency, created_at, closed_at, archive_path, assigned_to
        cursor.execute(f"SELECT * FROM tickets WHERE id=21")
        ticket_row = cursor.fetchall()
        print("Ticket search result:", ticket_row)

        conn.close()
    except Exception as e:
        print(f"Error inspecting DB: {e}")

if __name__ == "__main__":
    inspect_db()
