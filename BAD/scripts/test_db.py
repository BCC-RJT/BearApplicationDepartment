
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src import db

def test_db():
    print("Testing DB connection...")
    try:
        db.init_db()
        print("DB Initialized.")
    except Exception as e:
        print(f"DB Init Failed: {e}")
        return

    print("Testing Ticket Creation...")
    try:
        tid = db.create_ticket_record("pending", "123", "456", "TestUser")
        print(f"Ticket Created: {tid}")
    except Exception as e:
        print(f"Ticket Creation Failed: {e}")
        return
        
    print("Testing Ticket Update...")
    try:
        db.update_ticket_status("pending", "draft") # This updates by channel_id='pending'
        print("Ticket Updated Status.")
    except Exception as e:
        print(f"Ticket Update Failed: {e}")

if __name__ == "__main__":
    test_db()
