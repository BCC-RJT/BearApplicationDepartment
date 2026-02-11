import argparse
import sys
import os
import sqlite3
from datetime import datetime

# Adjust path to find src
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import db

def list_conversations(status=None):
    """Lists conversations."""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, channel_id, topic, status, created_at FROM conversations"
    params = []
    
    if status:
        query += " WHERE status = ?"
        params.append(status)
        
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    print(f"{'ID':<5} {'Channel':<20} {'Status':<10} {'Created At':<20} {'Topic'}")
    print("-" * 80)
    for row in rows:
        created_at = row['created_at']
        print(f"{row['id']:<5} {row['channel_id']:<20} {row['status']:<10} {created_at:<20} {row['topic']}")
    print("-" * 80)
    print(f"Total: {len(rows)}")

def delete_conversation(conversation_id):
    """Deletes a single conversation."""
    confirm = input(f"⚠️  Are you sure you want to PERMANENTLY delete conversation {conversation_id}? [y/N] ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    db.delete_conversation(conversation_id)
    print(f"✅ Conversation {conversation_id} deleted.")

def delete_all_closed():
    """Deletes all closed conversations."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM conversations WHERE status = 'closed'")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        print("No closed conversations found.")
        return

    confirm = input(f"⚠️  Are you sure you want to PERMANENTLY delete ALL {count} closed conversations? [y/N] ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return
        
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations WHERE status = 'closed'")
    ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    for cid in ids:
        db.delete_conversation(cid)
        
    print(f"✅ Deleted {count} closed conversations.")

def close_conversation(conversation_id):
    """Closes a single conversation."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM conversations WHERE id = ?", (conversation_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Conversation {conversation_id} not found.")
        conn.close()
        return
        
    if row['status'] == 'closed':
        print(f"⚠️ Conversation {conversation_id} is already closed.")
        conn.close()
        return
        
    conn.close()
    
    db.close_conversation(conversation_id)
    print(f"✅ Conversation {conversation_id} closed.")

def close_all_active():
    """Closes all active conversations."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM conversations WHERE status = 'active'")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        print("No active conversations found.")
        return

    confirm = input(f"⚠️  Are you sure you want to CLOSE ALL {count} active conversations? [y/N] ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return
        
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM conversations WHERE status = 'active'")
    ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    
    for cid in ids:
        db.close_conversation(cid)
        
    print(f"✅ Closed {count} active conversations.")

def main():
    parser = argparse.ArgumentParser(description="Manage conversations in the B.A.D. database.")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List conversations')
    list_parser.add_argument('--status', choices=['active', 'closed'], help='Filter by status')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a conversation')
    delete_parser.add_argument('id', type=int, help='Conversation ID to delete')
    
    # Close command
    close_parser = subparsers.add_parser('close', help='Close a conversation')
    close_parser.add_argument('id', type=int, help='Conversation ID to close')
    
    # Delete all closed command
    subparsers.add_parser('delete-all-closed', help='Delete all closed conversations')

    # Close all active command
    subparsers.add_parser('close-all-active', help='Close all active conversations')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_conversations(args.status)
    elif args.command == 'delete':
        delete_conversation(args.id)
    elif args.command == 'close':
        close_conversation(args.id)
    elif args.command == 'delete-all-closed':
        delete_all_closed()
    elif args.command == 'close-all-active':
        close_all_active()
    else:
        parser.print_help()

if __name__ == "__main__":
    db.init_db() # Ensure DB is initialized
    main()
