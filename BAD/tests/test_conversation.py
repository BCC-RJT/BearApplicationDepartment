import pytest
import os
import sqlite3
from src import db
from src.agent.conversation_manager import ConversationManager

# Use a test database
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'test_bad.db')

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    original_db_path = db.DB_PATH
    db.DB_PATH = TEST_DB_PATH
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    db.init_db()
    
    yield
    
    # Teardown
    db.DB_PATH = original_db_path
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass # Windows file locking sometimes

def test_conversation_creation():
    cm = ConversationManager()
    channel_id = "test_channel_1"
    
    # Should create new
    conv = cm.get_or_create_conversation(channel_id, "Hello World")
    assert conv is not None
    assert conv['channel_id'] == "test_channel_1"
    assert conv['topic'] == "Hello World"
    assert conv['status'] == 'active'

    # Should retreive existing
    conv2 = cm.get_or_create_conversation(channel_id, "New Topic")
    assert conv2['id'] == conv['id']
    
def test_message_flow():
    cm = ConversationManager()
    channel_id = "test_channel_2"
    
    # Add user message (triggers creation)
    cm.add_user_message(channel_id, "User Message 1")
    
    # Add bot message
    cm.add_bot_message(channel_id, "Bot Reply 1")
    
    # Check history
    history = cm.get_history(channel_id)
    assert len(history) == 2
    assert history[0] == "User: User Message 1"
    assert history[1] == "Bot: Bot Reply 1"

def test_reset_conversation():
    cm = ConversationManager()
    channel_id = "test_channel_3"
    
    cm.add_user_message(channel_id, "Msg 1")
    conv1 = cm.get_or_create_conversation(channel_id)
    
    # Reset
    assert cm.start_new_conversation(channel_id) == True
    
    # Create new
    cm.add_user_message(channel_id, "Msg 2")
    conv2 = cm.get_or_create_conversation(channel_id)
    
    assert conv1['id'] != conv2['id']
    
    # History should only show new conversation
    history = cm.get_history(channel_id)
    assert len(history) == 1
    assert history[0] == "User: Msg 2"
