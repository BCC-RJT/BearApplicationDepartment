
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add source path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

class TestDiscardFeature(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock socket to prevent singleton lock exit
        # Socket patch removed to avoid asyncio conflict


        # Mock discord to prevent runtime errors and connection attempts
        mock_discord = MagicMock()
        # Create a dummy View class to avoid MagicMock inheritance messing up async methods
        class MockView: 
            def __init__(self, timeout=None): self.children = []
            def add_item(self, item): pass
            @classmethod
            def __init_subclass__(cls, **kwargs): pass
        mock_discord.ui.View = MockView
        mock_discord.ui.Modal = MockView # Modal also needs to be a class
        
        # We need mock_discord.ui.button to be a decorator
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

        
        # safe default env vars using patch.dict
        self.env_patcher = patch.dict(os.environ, {
            'TICKET_MANAGER_INBOX_ID': '0',
            'TICKET_INCOMING_ID': '0',
            'TICKET_ACTIVE_ID': '0',
            'TICKET_BLOCKED_ID': '0',
            'TICKET_ARCHIVES_ID': '0',
            'PLANNING_CHANNEL_ID': '0',
            'DISCORD_TOKEN': 'mock_token'
        })
        self.env_patcher.start()

    def tearDown(self):

        self.discord_patcher.stop()
        self.env_patcher.stop()
        # Clean up imported module to allow re-import if needed
        if 'src.bridge.tickets_assistant' in sys.modules:
            del sys.modules['src.bridge.tickets_assistant']

    def test_discard_view_exists(self):
        """Test that DiscardView class exists in tickets_assistant module."""
        try:
            from src.bridge import tickets_assistant
        except SystemExit:
            self.fail("tickets_assistant called sys.exit() during import")
        except Exception as e:
            self.fail(f"tickets_assistant raised exception during import: {e}")

        self.assertTrue(hasattr(tickets_assistant, 'DiscardView'), "DiscardView class not found in tickets_assistant")

    async def test_discard_moves_to_archive(self):
        """Test that clicking discard moves the channel to archives instead of deleting it."""
        try:
            from src.bridge import tickets_assistant
        except ImportError:
            self.fail("Could not import tickets_assistant")

        # Setup Mocks
        view = tickets_assistant.DiscardView()
        
        mock_interaction = MagicMock()
        mock_channel = MagicMock()
        mock_guild = MagicMock()
        mock_category = MagicMock()
        mock_category.name = "Archives"
        
        mock_interaction.channel = mock_channel
        mock_interaction.guild = mock_guild
        mock_interaction.response = MagicMock()
        mock_interaction.response.send_message = MagicMock() # Mock async?
        
        # Async mocks require a bit more setup if they are awaited
        # But send_message is often just fire-and-forget in mocks unless we use AsyncMock
        # Let's use AsyncMock for everything async
        from unittest.mock import AsyncMock
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.message = MagicMock()
        mock_interaction.message.edit = AsyncMock()
        mock_channel.delete = AsyncMock()
        mock_channel.edit = AsyncMock()
        mock_channel.send = AsyncMock()
        
        # Situation A: CLOSED_ARCHIVES_ID is set (we mocked it to '0' in env)
        # tickets_assistant.CLOSED_ARCHIVES_ID should be 0
        # So guild.get_channel(0) should return our category
        mock_guild.get_channel.return_value = mock_category
        
        # Run the method
        await view.discard_button(mock_interaction, MagicMock())
        
        # Assertions for EXPECTED behavior (Moves to archive)
        # This should FAIL on the current code (which deletes)
        mock_channel.edit.assert_called_with(category=mock_category)
        mock_channel.delete.assert_not_called()

    async def test_discard_finds_closed_archives_by_name(self):
        """Test that clicking discard finds '🗄️ Closed Archives' if ID lookup fails."""
        from src.bridge import tickets_assistant
        
        view = tickets_assistant.DiscardView()
        
        mock_interaction = MagicMock()
        mock_channel = MagicMock()
        mock_guild = MagicMock()
        mock_category = MagicMock()
        mock_category.name = "🗄️ Closed Archives"
        
        mock_interaction.channel = mock_channel
        mock_interaction.guild = mock_guild
        # Async mocks
        from unittest.mock import AsyncMock
        mock_interaction.response.defer = AsyncMock()
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.message = MagicMock()
        mock_interaction.message.edit = AsyncMock()
        mock_channel.edit = AsyncMock()
        mock_channel.send = AsyncMock()
        
        # Determine get_channel failure (ID is 0)
        mock_guild.get_channel.return_value = None
        
        # Determine get_channel behavior via side_effect or get
        # discord.utils.get(guild.categories, name=X)
        # We need to mock discord.utils.get to return our mock_category when name matches
        
        original_get = tickets_assistant.discord.utils.get
        
        def side_effect_get(iterable, **kwargs):
            if kwargs.get('name') == "🗄️ Closed Archives":
                return mock_category
            return None
            
        tickets_assistant.discord.utils.get = side_effect_get
        
        try:
            await view.discard_button(mock_interaction, MagicMock())
            mock_channel.edit.assert_called_with(category=mock_category)
        finally:
            tickets_assistant.discord.utils.get = original_get

if __name__ == '__main__':
    unittest.main()
