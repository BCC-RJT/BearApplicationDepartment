import sys
import os
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mock modules that might cause import errors or side effects
sys.modules['database'] = MagicMock()
sys.modules['ai_handler'] = MagicMock()
sys.modules['drive_service'] = MagicMock()

# Now import the bot class
# We need to mock discord before importing main if main executes code at module level
# But main.py defines classes, so it should be fine if we mock dependencies
# valid_token is needed for bot instantiation? No, only run.

with patch.dict(os.environ, {'DISCORD_TOKEN': 'mock_token', 'GOOGLE_API_KEY': 'mock_key'}):
    # we need to ensure correct import path. 
    # main.py is in src/ticket_bot/main.py
    # and it does `from database import ...` which assumes ticket_bot is in path or run as module
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'ticket_bot')))
    from ticket_bot.main import TicketBot, NewTicketView

class TestDiscardTicket(unittest.IsolatedAsyncioTestCase):
    async def test_create_ticket_channel_sends_separate_discard_msg(self):
        # Setup
        bot = TicketBot()
        bot.db = MagicMock()
        bot.category_cache = {'manager': MagicMock()}
        
        user = MagicMock()
        user.name = "TestUser"
        user.mention = "@TestUser"
        user.guild = MagicMock()
        
        channel = AsyncMock()
        channel.id = 12345
        channel.mention = "#ticket-test"
        user.guild.create_text_channel = AsyncMock(return_value=channel)
        
        # Execute
        await bot.create_ticket_channel(user)
        
        # Verify
        # We expect TWO calls to channel.send
        # 1. Control Panel (with View)
        # 2. Greeting (without View, or different view)
        
        # Current implementation has 1 call. This test expects failure initially.
        self.assertEqual(channel.send.call_count, 2, "Should send 2 messages: Controls then Greeting")
        
        # Check first message (Controls)
        args, kwargs = channel.send.call_args_list[0]
        # We expect a view in the first message
        self.assertIn('view', kwargs, "First message should have the Discard view")
        self.assertIsInstance(kwargs['view'], NewTicketView)
        
        # Check second message (Greeting)
        args2, kwargs2 = channel.send.call_args_list[1]
        self.assertIn("Hello", args2[0], "Second message should be the greeting")
        # Ensure greeting does NOT have the Discard view (or at least not the same one, but ideally none or standard)
        # The prompt implies "before the initial greeting", so greeting follows.

if __name__ == '__main__':
    unittest.main()
