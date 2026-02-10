import pytest
import sqlite3
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_discord_ctx():
    """Mocks a Discord Context object."""
    ctx = AsyncMock()
    ctx.author.id = 123456789
    ctx.channel.send = AsyncMock()
    ctx.message.content = "!test"
    return ctx

@pytest.fixture
def mock_gemini():
    """Mocks the Google Generative AI model."""
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=MagicMock(text='{"status": "COMPLETE"}'))
    return mock_model

@pytest.fixture
def mock_drive():
    """Mocks the Google Drive API service."""
    mock_service = MagicMock()
    return mock_service

@pytest.fixture
def mock_db():
    """Creates an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    # Setup schema (simplified for testing)
    cursor.execute("CREATE TABLE tickets (id INTEGER PRIMARY KEY, user_id INTEGER, status TEXT)")
    conn.commit()
    yield conn
    conn.close()
