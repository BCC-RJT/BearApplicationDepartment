
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add source path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# We need to mock sqlite3 for unit tests if we don't want to write to disk
# But for integration, using a temporary DB file is better.
# Let's patch db.DB_PATH to use a temp file.

class TestTicketDBIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock discord imports first
        mock_discord = MagicMock()
        class MockView: 
            def __init__(self, timeout=None): self.children = []
            def add_item(self, item): pass
            @classmethod
            def __init_subclass__(cls, **kwargs): pass
        mock_discord.ui.View = MockView
        mock_discord.ui.Modal = MockView
        
        def mock_button(**kwargs):
            def decorator(func):
                return func
            return decorator
        mock_discord.ui.button = mock_button
        
        self.discord_patcher = patch.dict(sys.modules, {
            'discord': mock_discord, 
            'discord.ui': mock_discord.ui,
            'discord.ext': MagicMock()
        })
        self.discord_patcher.start()

        # Mock env
        self.env_patcher = patch.dict(os.environ, {
            'DISCORD_TOKEN': 'mock_token'
        })
        self.env_patcher.start()

        # Import DB module now
        from src import db
        import tempfile
        
        # Setup temp DB
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = self.db_path
        db.init_db()

    def tearDown(self):
        from src import db
        db.DB_PATH = self.original_db_path
        os.close(self.db_fd)
        os.remove(self.db_path)
        self.discord_patcher.stop()
        self.env_patcher.stop()
        
        # Clean up modules
        if 'src.bridge.tickets_assistant' in sys.modules:
            del sys.modules['src.bridge.tickets_assistant']

    async def test_create_ticket_generates_id(self):
        """Test that updating ticket workflow creates a DB record."""
        from src import db
        from src.bridge import tickets_assistant
        
        # We need to verify create_ticket_record works
        # And that if we simulate the bot's flow, it calls it.
        # Simulating flow is hard without full bot setup.
        # Let's test the DB functions directly first.
        
        tid = db.create_ticket_record("chan-123", "guild-1", "user-1", "user-name")
        self.assertIsNotNone(tid)
        
        ticket = db.get_ticket("chan-123")
        self.assertEqual(ticket['user_name'], "user-name")
        self.assertEqual(ticket['status'], 'draft')
        
    async def test_update_ticket_status(self):
        from src import db
        tid = db.create_ticket_record("chan-456", "guild-1", "user-2", "user-name")
        
        db.update_ticket_status("chan-456", "active")
        ticket = db.get_ticket("chan-456")
        self.assertEqual(ticket['status'], "active")
        
    async def test_update_ticket_details(self):
        from src import db
        tid = db.create_ticket_record("chan-789", "guild-1", "user-3", "user-name")
        
        db.update_ticket_details("chan-789", "New Title", "New Desc", "High")
        ticket = db.get_ticket("chan-789")
        self.assertEqual(ticket['title'], "New Title")
        self.assertEqual(ticket['urgency'], "High")

if __name__ == '__main__':
    unittest.main()
