
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestTicketGreeting(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch socket
        self.patcher_socket = patch('socket.socket')
        self.patcher_socket.start()

        # Create a Dummy View class to avoid MagicMock inheritance issues
        class DummyView:
            def __init__(self, *args, **kwargs):
                self.children = [] # Simulate View.children
            
            def add_item(self, item):
                self.children.append(item)
                
        # Mock discord.ui.button decorator to pass through the function
        def mock_button_decorator(*args, **kwargs):
             def decorator(func):
                 return func
             return decorator

        # Mock discord module
        self.mock_discord = MagicMock()
        self.mock_discord.ui.View = DummyView
        self.mock_discord.ui.button.side_effect = mock_button_decorator
        self.mock_discord.ButtonStyle = MagicMock()
        self.mock_discord.Embed = MagicMock() # Mock the class itself
        
        # Patch sys.modules to return our mock discord
        self.patcher_discord_mod = patch.dict(sys.modules, {
            'discord': self.mock_discord, 
            'discord.ui': self.mock_discord.ui,
            'discord.ext': MagicMock()
        })
        self.patcher_discord_mod.start()

        # Mock os.environ
        self.patcher_env = patch.dict(os.environ, {
             'TICKET_MANAGER_INBOX_ID': '0',
             'TICKET_INCOMING_ID': '0',
             'TICKET_ACTIVE_ID': '0', 
             'TICKET_BLOCKED_ID': '0', 
             'TICKET_ARCHIVES_ID': '0',
             'PLANNING_CHANNEL_ID': '0',
             'DISCORD_TOKEN': 'mock_token'
        })
        self.patcher_env.start()
        
        # Import target module
        # Force reload if already imported to ensure it uses our patched discord
        if 'src.bridge.tickets_assistant' in sys.modules:
            del sys.modules['src.bridge.tickets_assistant']
            
        from src.bridge import tickets_assistant
        self.module = tickets_assistant
        
        # Ensure conversation_manager is set so we enter the if block
        self.module.conversation_manager = MagicMock()

    def tearDown(self):
        self.patcher_socket.stop()
        self.patcher_discord_mod.stop()
        self.patcher_env.stop()
        if 'src.bridge.tickets_assistant' in sys.modules:
            del sys.modules['src.bridge.tickets_assistant']

    async def test_create_ticket_sends_correct_greeting(self):
        # Setup Interaction Mock
        interaction = MagicMock()
        interaction.user.mention = "@User"
        interaction.user.name = "TestUser"
        interaction.guild = MagicMock()
        interaction.response = MagicMock()
        interaction.response.send_message = AsyncMock()
        interaction.response.defer = AsyncMock()
        interaction.delete_original_response = AsyncMock()
        
        # Mock Channel Creation
        mock_channel = MagicMock()
        mock_channel.id = 12345
        mock_channel.send = AsyncMock()
        interaction.guild.create_text_channel = AsyncMock(return_value=mock_channel)
        
        # Initialize View
        view = self.module.TicketView()
        
        # Execute
        await view.create_ticket(interaction, MagicMock())
        
        # Verify Channel Created
        interaction.guild.create_text_channel.assert_called_once()
        
        # Verify Send Calls
        # Should be called twice now: once for greeting+embed, once for question
        self.assertEqual(mock_channel.send.call_count, 2)
        
        # Get calls
        calls = mock_channel.send.call_args_list
        
        # --- Check Message 1 (Greeting + Embed) ---
        call1 = calls[0]
        kwargs1 = call1.kwargs
        args1 = call1.args
        content1 = kwargs1.get('content') or (args1[0] if args1 else None)
        
        self.assertIn("Hey", content1)
        self.assertIn("Ticket Assistant", content1)
        self.assertIn("@User", content1)
        
        # Check Embed in Call 1
        embed_arg = kwargs1.get('embed')
        self.assertIsNotNone(embed_arg, "Embed should be sent in first message")
        self.mock_discord.Embed.assert_called_with(
            title="Ticket Controls",
            description="If you created this by mistake, just hit the button below to discard it.",
            color=self.mock_discord.Color.red()
        )
        
        # --- Check Message 2 (Question) ---
        call2 = calls[1]
        kwargs2 = call2.kwargs
        args2 = call2.args
        content2 = kwargs2.get('content') or (args2[0] if args2 else None)
        
        self.assertIn("So, what's going on?", content2)
        self.assertIn("issue is", content2)
        self.assertIn("when you need this done by", content2)
        
        # Ensure no embed in second message
        self.assertIsNone(kwargs2.get('embed'), "Second message should not have an embed")

if __name__ == '__main__':
    unittest.main()
