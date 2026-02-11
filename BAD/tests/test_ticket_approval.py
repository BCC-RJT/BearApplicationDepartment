
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add source path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestTicketApproval(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock discord imports
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
        
        # Mock env vars
        self.env_patcher = patch.dict(os.environ, {
            'TICKET_MANAGER_INBOX_ID': '0', # Force fallback to name lookup
            'DISCORD_TOKEN': 'mock_token'
        })
        self.env_patcher.start()

    def tearDown(self):
        self.discord_patcher.stop()
        self.env_patcher.stop()
        if 'src.bridge.tickets_assistant' in sys.modules:
            del sys.modules['src.bridge.tickets_assistant']

    async def test_submit_ticket_moves_to_ticket_inbox(self):
        """Test that submitting a ticket moves it to 'Ticket Inbox' category."""
        from src.bridge import tickets_assistant
        
        # Setup View
        title = "Test Ticket"
        urgency = "High" 
        description = "Test Description"
        view = tickets_assistant.ProposalView(title, urgency, description)
        
        # Setup Mocks
        mock_interaction = MagicMock()
        mock_channel = MagicMock()
        mock_guild = MagicMock()
        mock_category = MagicMock()
        mock_category.name = "Ticket Inbox"
        
        mock_interaction.channel = mock_channel
        mock_interaction.guild = mock_guild
        mock_channel.name = "incoming-user" # Should be renamed to ticket-user
        
        # Async mocks
        from unittest.mock import AsyncMock
        mock_interaction.response.defer = AsyncMock()
        mock_channel.edit = AsyncMock()
        mock_channel.send = AsyncMock()
        mock_interaction.message.edit = AsyncMock()
        
        # Mock guild.get_channel(0) -> None
        mock_guild.get_channel.return_value = None
        
        # Mock finding category by name
        def side_effect_get(iterable, **kwargs):
            if kwargs.get('name') == "Ticket Inbox":
                return mock_category
            return None
        tickets_assistant.discord.utils.get = side_effect_get
        
        # Run
        await view.submit_ticket(mock_interaction, MagicMock())
        
        # Verify 
        # 1. Moved to correct category
        mock_channel.edit.assert_any_call(category=mock_category)
        
        # 2. Renamed channel
        mock_channel.edit.assert_any_call(name="ticket-user")

if __name__ == '__main__':
    unittest.main()
