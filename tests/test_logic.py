import unittest
import json
from unittest.mock import AsyncMock, MagicMock

# Mock implementation (same as before)
async def handle_interview(ctx, model, db):
    response = await model.generate_content_async(ctx.message.content)
    data = json.loads(response.text)
    if data.get("status") == "COMPLETE":
        await ctx.channel.send("Ticket Created")
    elif data.get("status") == "INCOMPLETE":
        await ctx.channel.send("Follow-up question")

async def move_ticket(ticket_id, new_status, db):
    db.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
    db.commit()

class TestLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_discord_ctx = AsyncMock()
        self.mock_discord_ctx.author.id = 123456789
        self.mock_discord_ctx.channel.send = AsyncMock()
        self.mock_discord_ctx.message.content = "!test"

        self.mock_gemini = MagicMock()
        self.mock_gemini.generate_content_async = AsyncMock(return_value=MagicMock(text='{"status": "COMPLETE"}'))

        # Simple Mock DB
        self.mock_db = MagicMock()
        self.mock_db.execute = MagicMock()
        self.mock_db.commit = MagicMock()

    async def test_interview_complete(self):
        """Test A: Verify valid JSON triggers Ticket Creation."""
        self.mock_gemini.generate_content_async.return_value.text = '{"status": "COMPLETE"}'
        
        await handle_interview(self.mock_discord_ctx, self.mock_gemini, self.mock_db)
        
        self.mock_discord_ctx.channel.send.assert_called_with("Ticket Created")

    async def test_interview_incomplete(self):
        """Test B: Verify incomplete status triggers follow-up."""
        self.mock_gemini.generate_content_async.return_value.text = '{"status": "INCOMPLETE"}'
        
        await handle_interview(self.mock_discord_ctx, self.mock_gemini, self.mock_db)
        
        self.mock_discord_ctx.channel.send.assert_called_with("Follow-up question")

    async def test_state_transitions(self):
        """Test C: Verify status update."""
        # For this test we can stick to MagicMock verification for the execute call
        await move_ticket(1, 'Active', self.mock_db)
        
        self.mock_db.execute.assert_called_with("UPDATE tickets SET status = ? WHERE id = ?", ('Active', 1))
