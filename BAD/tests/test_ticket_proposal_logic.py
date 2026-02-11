import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock modules that might fail to import due to path issues
sys.modules['drive_service'] = MagicMock()
sys.modules['database'] = MagicMock()
# sys.modules['ai_handler'] = MagicMock() # We need to mock this carefully or just let it import if possible.
# ai_handler imports google.generativeai, dotenv. Should be fine if env is ok.
# But ai_handler is in ticket_bot/, so check if it imports ok.
# It is imported as: from ai_handler import get_ai_response
# So we need to mock it too.
sys.modules['ai_handler'] = MagicMock()

# Now we can import main
# But wait, main.py does: from ai_handler import get_ai_response
# If we mock ai_handler, main.py will get the mock.
from ticket_bot.main import TicketBot, TicketProposalView

import asyncio

@pytest.fixture
def mock_bot():
    bot = TicketBot()
    bot.db = MagicMock()
    # bot.user is a property, returns _user
    bot._user = MagicMock() 
    bot._user.id = 8888
    bot.process_commands = AsyncMock() # Mock this to avoid internal checks on message
    return bot

def test_on_message_ignores_self(mock_bot):
    async def run_test():
        message = AsyncMock()
        message.author = mock_bot.user
        
        await mock_bot.on_message(message)
        
        # Should check if any processing happened, but mostly just ensuring no crash
        # and no AI calls
        assert not message.channel.send.called
    
    asyncio.run(run_test())

def test_on_message_proposes_ticket(mock_bot):
    async def run_test():
        # Setup
        message = AsyncMock()
        message.id = 10001 # Set ID
        message.author.id = 123
        message.author.bot = False
        message.content = "I have a bug"
        message.channel.id = 999
        message.guild.me = MagicMock()
        

        # Fix typing() mock to be an async context manager
        typing_cm = MagicMock()
        async def async_context_manager():
            yield
            
        # Actually simplest way to mock async context manager is modifying __aenter__ and __aexit__
        typing_cm.__aenter__.return_value = None
        typing_cm.__aexit__.return_value = None
        
        # Make typing a helper that returns the cm
        message.channel.typing = MagicMock(return_value=typing_cm)

        # Mock DB to say this is a ticket channel
        # ticket schema: ticket_id, channel_id, user_id, user_name, helper_id, status...
        # status is index 5.
        mock_bot.db.get_ticket_by_channel.return_value = (999, 999, 123, "User", None, "setup")
        
        # Mock History
        # Async iterator mock
        class AsyncIter:
            def __init__(self, items):
                self.items = items
            def __aiter__(self):
                self.iter = iter(self.items)
                return self
            async def __anext__(self):
                try:
                    return next(self.iter)
                except StopIteration:
                    raise StopAsyncIteration

        # We need a fresh mock for history call because main.py calls history(limit=20)
        # message.channel.history returns the async iterator
        # IMPORTANT: history includes the message itself usually
        message.channel.history = MagicMock(return_value=AsyncIter([message]))

        # Mock AI Handler
        with patch('ticket_bot.main.get_ai_response', new_callable=AsyncMock) as mock_get_ai:
            with patch('ticket_bot.main.parse_ticket_data') as mock_parse:
                # Case 1: Not Ready
                mock_get_ai.return_value = "What is the bug?"
                mock_parse.return_value = (False, None, "What is the bug?")
                
                await mock_bot.on_message(message)
                
                # Should send AI response
                message.channel.send.assert_called_with("What is the bug?")
                
                # Reset mock for Case 2
                message.channel.send.reset_mock()

                # Case 2: Ready
                mock_get_ai.return_value = "Ticket Ready JSON"
                mock_parse.return_value = (True, {
                    "ticket_ready": True, 
                    "issue_type": "Bug", 
                    "description": "It crashes", 
                    "expected_outcome": "It works", 
                    "priority": "High"
                }, "Summary")
                
                await mock_bot.on_message(message)
                
                # Should send Embed with View
                args, kwargs = message.channel.send.call_args
                assert kwargs.get('view') is not None
                assert isinstance(kwargs['view'], TicketProposalView)
                assert kwargs.get('embed') is not None
                assert kwargs['embed'].title == "Ticket Proposal"

    asyncio.run(run_test())

