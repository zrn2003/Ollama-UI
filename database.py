import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establish connection to YugabyteDB"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('YUGABYTE_HOST', 'us-east-1.caf91660-4797-4dec-91fd-a282ebb4037b.aws.yugabyte.cloud'),
            port=int(os.getenv('YUGABYTE_PORT', '5433')),
            database=os.getenv('YUGABYTE_DB', 'yugabyte'),
            user=os.getenv('YUGABYTE_USER', 'admin'),
            password=os.getenv('YUGABYTE_PASSWORD', 'cXgvtpIzCjd2yfjoTW-ed8TFhqP3qi'),
            connect_timeout=10
        )
        logger.info("Database connection established successfully")
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def initialize_database():
    """Create database tables and indexes if they don't exist"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title VARCHAR(255) NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Create messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    );
                """)

                # Create indexes for performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                    ON conversations(updated_at DESC);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                    ON messages(conversation_id, created_at ASC);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_time
                    ON messages(conversation_id, created_at DESC);
                """)

                conn.commit()
                logger.info("Database tables and indexes created successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Conversation operations
def create_conversation(title: str, provider: str, model: str) -> str:
    """Create a new conversation and return its ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO conversations (title, provider, model)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (title, provider, model))
                conversation_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Created conversation: {conversation_id}")
                return str(conversation_id)
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise

def get_conversations(limit: int = 50) -> List[Dict]:
    """Get list of recent conversations"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, title, provider, model, created_at, updated_at
                    FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT %s;
                """, (limit,))
                conversations = cursor.fetchall()
                return [dict(conv) for conv in conversations]
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        return []

def get_conversation(conversation_id: str) -> Optional[Dict]:
    """Get a specific conversation by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, title, provider, model, created_at, updated_at
                    FROM conversations
                    WHERE id = %s;
                """, (conversation_id,))
                conversation = cursor.fetchone()
                return dict(conversation) if conversation else None
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        return None

def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Update conversation title"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE conversations
                    SET title = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (title, conversation_id))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update conversation title: {e}")
        return False

def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM conversations WHERE id = %s;", (conversation_id,))
                conn.commit()
                return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        return False

# Message operations
def save_message(conversation_id: str, role: str, content: str) -> str:
    """Save a message and return its ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (conversation_id, role, content))
                message_id = cursor.fetchone()[0]

                # Update conversation timestamp
                cursor.execute("""
                    UPDATE conversations
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (conversation_id,))

                conn.commit()
                return str(message_id)
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        raise

def get_messages(conversation_id: str) -> List[Dict]:
    """Get all messages for a conversation"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, conversation_id, role, content, created_at
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC;
                """, (conversation_id,))
                messages = cursor.fetchall()
                return [dict(msg) for msg in messages]
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
        return []

def generate_conversation_title(messages: List[Dict]) -> str:
    """Generate a title from the first user message"""
    if not messages:
        return "New Conversation"

    # Find the first user message
    for msg in messages:
        if msg['role'] == 'user':
            content = msg['content'].strip()
            # Take first 50 characters or first line
            title = content.split('\n')[0][:50]
            if len(title) < len(content.split('\n')[0]):
                title += "..."
            return title or "New Conversation"

    return "New Conversation"
