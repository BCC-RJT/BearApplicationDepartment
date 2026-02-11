
import sqlite3

db_path = "data/bad.db"

def inspect_db():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)
        
        for table in tables:
            table_name = table[0]
            print(f"\n--- {table_name} ---")
            # Get columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print("Columns:", columns)
            
            # Get first 5 rows
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
                
            # If there is a tickets table, search for 'ticket-21-rtmoney' or just '21'
            if table_name == "tickets":
                print(f"\nSearching for ticket 'ticket-21-rtmoney' in {table_name}...")
                cursor.execute(f"SELECT * FROM {table_name} WHERE channel_name LIKE '%ticket-21%' OR id=21")
                ticket_row = cursor.fetchall()
                print("Ticket search result:", ticket_row)

        conn.close()
    except Exception as e:
        print(f"Error inspecting DB: {e}")

if __name__ == "__main__":
    inspect_db()
