
import sqlite3
import os
import sys

# Add src to path just in case, though we will access DB directly
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'bad.db')

def read_ticket():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    print(f"📂 Reading from {DB_PATH}...\n")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Get latest active conversation
    cursor.execute('''
        SELECT * FROM conversations 
        WHERE status = 'active' 
        ORDER BY created_at DESC 
        LIMIT 1
    ''')
    conversation = cursor.fetchone()
    
    if not conversation:
        print("📭 No active ticket/conversation found in the database.")
        conn.close()
        return

    print(f"🎫 **Active Conversation Found**")
    print(f"ID: {conversation['id']}")
    print(f"Channel ID: {conversation['channel_id']}")
    print(f"Topic: {conversation['topic']}")
    print(f"Started: {conversation['created_at']}")
    print("-" * 40)
    
    # 2. Get Messages
    cursor.execute('''
        SELECT role, content, created_at FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
    ''', (conversation['id'],))
    
    messages = cursor.fetchall()
    
    for msg in messages:
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        print(f"{role_icon} [{msg['created_at']}] {msg['role'].upper()}: {msg['content']}")
    
    conn.close()

if __name__ == "__main__":
    read_ticket()
