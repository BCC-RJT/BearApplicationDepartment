import logging
from src import db

logger = logging.getLogger("CONVERSATION_MANAGER")

class ConversationManager:
    def __init__(self):
        pass

    def get_or_create_conversation(self, channel_id, user_message=None):
        """
        Retrieves the active conversation for a channel, or creates a new one 
        if none exists (and we have a user message to start it with).
        """
        conversation = db.get_active_conversation(channel_id)
        
        if not conversation:
            # Start new conversation
            logger.info(f"Starting new conversation for channel {channel_id}")
            # Use first few words of message as topic, or default
            topic = "New Conversation"
            if user_message:
                topic = (user_message[:30] + '...') if len(user_message) > 30 else user_message
            
            conversation_id = db.create_conversation(channel_id, topic)
            conversation = db.get_active_conversation(channel_id) # Reload to get full object
            
        return conversation

    def add_user_message(self, channel_id, content):
        """Adds a user message to the active conversation."""
        conversation = self.get_or_create_conversation(channel_id, content)
        if conversation:
            db.add_message(conversation['id'], 'user', content)
            return conversation
        return None

    def add_bot_message(self, channel_id, content):
        """Adds a bot message to the active conversation."""
        conversation = db.get_active_conversation(channel_id)
        if conversation:
            db.add_message(conversation['id'], 'model', content)
        else:
            logger.warning(f"Attempted to add bot message to inactive conversation in {channel_id}")

    def get_history(self, channel_id):
        """Returns the conversation history formatted for the brain."""
        conversation = db.get_active_conversation(channel_id)
        if not conversation:
            return []
        
        messages = db.get_conversation_history(conversation['id'])
        formatted_history = []
        for msg in messages:
            role = "User" if msg['role'] == 'user' else "Bot"
            formatted_history.append(f"{role}: {msg['content']}")
            
        return formatted_history

    def start_new_conversation(self, channel_id):
        """Forces a new conversation by closing the old one."""
        old_conversation = db.get_active_conversation(channel_id)
        if old_conversation:
            db.close_conversation(old_conversation['id'])
            logger.info(f"Closed conversation {old_conversation['id']} for channel {channel_id}")
            return True
        return False

    def delete_conversation(self, channel_id, conversation_id=None):
        """
        Deletes a conversation.
        If conversation_id is provided, deletes that specific conversation.
        If only channel_id is provided, deletes the active conversation for that channel.
        """
        if conversation_id:
            db.delete_conversation(conversation_id)
            logger.info(f"Deleted conversation {conversation_id}")
            return True
            
        conversation = db.get_active_conversation(channel_id)
        if conversation:
            db.delete_conversation(conversation['id'])
            logger.info(f"Deleted active conversation {conversation['id']} for channel {channel_id}")
            return True
            
        return False
