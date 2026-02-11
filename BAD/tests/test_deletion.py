import unittest
import os
import sys
import sqlite3

# Adjust path to find src
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src import db
from src.agent.conversation_manager import ConversationManager

class TestConversationDeletion(unittest.TestCase):
    def setUp(self):
        self.test_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'test_deletion.db')
        self.original_db_path = db.DB_PATH
        db.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass
        db.init_db()

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_delete_conversation_active(self):
        """Test deleting the active conversation for a channel."""
        cm = ConversationManager()
        channel_id = "test_chan_del_1"
        
        # Create conversation and add messages
        cm.add_user_message(channel_id, "User Message 1")
        cm.add_bot_message(channel_id, "Bot Response 1")
        
        conv = cm.get_or_create_conversation(channel_id)
        conv_id = conv['id']
        
        # Verify existence
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversations WHERE id=?", (conv_id,))
        self.assertIsNotNone(cur.fetchone())
        cur.execute("SELECT * FROM messages WHERE conversation_id=?", (conv_id,))
        self.assertEqual(len(cur.fetchall()), 2)
        conn.close()
        
        # Delete Active
        result = cm.delete_conversation(channel_id)
        self.assertTrue(result)
        
        # Verify deletion
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversations WHERE id=?", (conv_id,))
        self.assertIsNone(cur.fetchone())
        cur.execute("SELECT * FROM messages WHERE conversation_id=?", (conv_id,))
        self.assertEqual(len(cur.fetchall()), 0)
        conn.close()

    def test_delete_specific_conversation_id(self):
        """Test deleting a generic conversation by ID (simulating admin tool)."""
        cm = ConversationManager()
        channel_id = "test_chan_del_2"
        
        # Create conversation
        cm.add_user_message(channel_id, "Test Msg")
        conv = cm.get_or_create_conversation(channel_id)
        conv_id = conv['id']
        
        # Close it (archive it)
        cm.start_new_conversation(channel_id)
        
        # Check it is closed
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM conversations WHERE id=?", (conv_id,))
        row = cur.fetchone()
        self.assertEqual(row['status'], 'closed')
        conn.close()
        
        # Delete by ID
        db.delete_conversation(conv_id)
        
        # Verify deletion
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversations WHERE id=?", (conv_id,))
        self.assertIsNone(cur.fetchone())
        conn.close()

if __name__ == '__main__':
    unittest.main()
