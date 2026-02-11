import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Add src to path
# Assuming run from BAD/tests or BAD
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    import src.db as db
except ImportError:
    try:
        import db
    except ImportError:
        print("❌ Could not import db module by any means.")
        sys.exit(1)

# Use temp file DB for testing logic without affecting real data
import tempfile
tf = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tf.close()
db.DB_PATH = tf.name

def setup_db():
    db.init_db()

def test_logic():
    print("🧪 Setting up DB...")
    setup_db()
    
    conn = db.get_connection()
    c = conn.cursor()
    
    # scenario:
    # 5 Old tickets (2 weeks old) -> Should be archived due to age (AND index if low priority, but here Age checks first if we implement correctly, or Index checks first).
    # My logic: Check Index first. Then Age.
    # Order: date DESC. So Recent are top. Old are bottom.
    
    # 55 Recent tickets (1 hour old).
    
    print("📝 Inserting dummy tickets...")
    
    # Insert Old Tickets (IDs old_0 to old_4)
    old_time = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    for i in range(5):
        c.execute("INSERT INTO tickets (channel_id, status, closed_at) VALUES (?, ?, ?)", (f"old_{i}", 'closed', old_time))
        
    # Insert Recent Tickets (IDs recent_0 to recent_54)
    recent_time = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    for i in range(55):
        c.execute("INSERT INTO tickets (channel_id, status, closed_at) VALUES (?, ?, ?)", (f"recent_{i}", 'closed', recent_time))
        
    conn.commit()
    conn.close()
    
    # Retrieve
    print("🔍 Fetching closed tickets...")
    closed_tickets = db.get_closed_tickets()
    print(f"   Total found: {len(closed_tickets)}")
    
    # Simulate Archiving Logic
    archived = []
    kept = []
    cutoff_date = datetime.now() - timedelta(days=7)
    
    print("⚙️ Running archiving logic...")
    for i, ticket in enumerate(closed_tickets):
        should_archive = False
        
        # Check 1: Count limit
        if i >= 50:
            should_archive = True
        
        # Check 2: Age limit
        if not should_archive:
            closed_at_str = ticket['closed_at']
            try:
                # Assuming format
                cat = datetime.strptime(closed_at_str, "%Y-%m-%d %H:%M:%S")
                if cat < cutoff_date:
                    should_archive = True
            except ValueError:
                pass
        
        if should_archive:
            archived.append(ticket['channel_id'])
            # Simulate DB update
            db.mark_ticket_archived(ticket['channel_id'])
        else:
            kept.append(ticket['channel_id'])
            
    print(f"   Archived: {len(archived)}")
    print(f"   Kept: {len(kept)}")
    
    # Verification
    # Expected: 50 Kept (The 50 most recent of the 55 recent ones).
    # Archived: 5 Recent (excess) + 5 Old (age + excess). Total 10.
    
    if len(kept) != 50:
        print(f"❌ FAILED: Expected 50 kept, got {len(kept)}")
    else:
        print("✅ Correct number of tickets kept (50).")

    if len(archived) != 10:
        print(f"❌ FAILED: Expected 10 archived, got {len(archived)}")
    else:
        print("✅ Correct number of tickets archived (10).")
        
    # Check specifics
    old_archived = len([t for t in archived if 'old' in t])
    recent_archived = len([t for t in archived if 'recent' in t])
    
    print(f"   Old Archived: {old_archived} (Expected 5)")
    print(f"   Recent Archived: {recent_archived} (Expected 5)")
    
    if old_archived == 5 and recent_archived == 5:
        print("✅ Logic Verified Correctly!")
    else:
        print("❌ Logic Validation Failed.")

if __name__ == "__main__":
    test_logic()
