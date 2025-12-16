# AI Multi-Provider Chat Application

A comprehensive, modern chat application that integrates multiple AI providers (Ollama, OpenAI ChatGPT, Google Gemini) with persistent conversation history stored in YugabyteDB. Features a clean, accessible interface with real-time chat capabilities.

## 🌟 Key Features

### 🤖 AI Integration
- **Multi-Provider Support**: Seamlessly switch between Ollama (local), OpenAI ChatGPT, and Google Gemini
- **Dynamic Model Selection**: Choose from available models for each provider
- **Real-time Responses**: Instant AI-generated replies with typing indicators
- **Fallback Handling**: Graceful error handling for API failures

### 💾 Database & Persistence
- **YugabyteDB Integration**: Distributed SQL database for reliable data storage
- **Persistent Conversations**: All chat history automatically saved
- **Session Management**: Independent conversation threads
- **Automatic Cleanup**: Efficient data management and indexing

### 🎨 User Interface
- **Modern Design**: Clean, professional interface with subtle animations
- **Accessibility First**: ARIA labels, keyboard navigation, screen reader support
- **Responsive Layout**: Optimized for desktop, tablet, and mobile devices
- **Dark Mode Support**: Automatic theme detection and switching
- **Touch-Friendly**: Optimized for touch interactions

### 🔧 Developer Features
- **Modular Architecture**: Clean separation of concerns
- **Environment Configuration**: Flexible API key management
- **Error Handling**: Comprehensive error reporting and recovery
- **Logging**: Detailed operation logs for debugging
- **Scalable Design**: Easy to extend with new AI providers

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended for local AI models)
- **Storage**: 1GB free space for application and dependencies

### Required Software
- **YugabyteDB**: Distributed SQL database (local installation or cloud instance)
- **Git**: Version control system
- **Python Virtual Environment**: venv or conda (recommended)

### AI Provider Requirements
- **Ollama** (for local AI): Download from [ollama.ai](https://ollama.ai)
- **OpenAI API Key** (for ChatGPT): Get from [platform.openai.com](https://platform.openai.com)
- **Google Gemini API Key** (for Gemini): Get from [makersuite.google.com](https://makersuite.google.com)

## 🚀 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd ai-chat-app
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

#### Option A: YugabyteDB Local Installation
1. **Download YugabyteDB** from [yugabyte.com](https://www.yugabyte.com/)
2. **Start YugabyteDB**:
   ```bash
   # Start single-node cluster
   ./bin/yugabyted start
   ```
3. **Create Database**:
   ```sql
   CREATE DATABASE chat_app;
   ```

#### Option B: YugabyteDB Cloud
1. **Sign up** at [cloud.yugabyte.com](https://cloud.yugabyte.com/)
2. **Create a cluster** and note the connection details
3. **Update environment variables** (see Configuration section)

### Step 5: Environment Configuration
Create a `.env` file in the project root:

```bash
# YugabyteDB Configuration
YUGABYTE_HOST=localhost
YUGABYTE_PORT=5433
YUGABYTE_DB=chat_app
YUGABYTE_USER=yugabyte
YUGABYTE_PASSWORD=password

# AI Provider API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
```

### Step 6: Initialize Database
```bash
# Run the database initialization script
python test_db.py
```

### Step 7: Start the Application
```bash
streamlit run UI.py
```

The application will open at `http://localhost:8501`

## 🗄️ Database Architecture

### Database Schema

#### `conversations` Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Fields:**
- `id`: Unique conversation identifier (UUID)
- `title`: Auto-generated conversation title from first message
- `provider`: AI provider ('Ollama', 'ChatGPT', 'Gemini')
- `model`: Specific model used (e.g., 'gpt-4', 'llama3.2')
- `created_at`: Conversation creation timestamp
- `updated_at`: Last modification timestamp

#### `messages` Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**Fields:**
- `id`: Unique message identifier (UUID)
- `conversation_id`: Foreign key to conversations table
- `role`: Message sender ('user' or 'assistant')
- `content`: Full message text content
- `created_at`: Message timestamp

### Indexes & Performance
```sql
-- Performance indexes
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id, created_at ASC);

-- Composite index for efficient conversation loading
CREATE INDEX idx_messages_conversation_time ON messages(conversation_id, created_at DESC);
```

### Data Flow
1. **User Input** → Message stored in `messages` table
2. **AI Processing** → Provider API called with conversation context
3. **AI Response** → Assistant message stored in `messages` table
4. **UI Update** → Conversation `updated_at` timestamp refreshed
5. **Persistence** → All data automatically saved to YugabyteDB

## 🎯 Usage Guide

### Getting Started
1. **Launch Application**: `streamlit run UI.py`
2. **Configure AI Provider**: Select provider and enter API keys in sidebar
3. **Start Chatting**: Click "➕ New Chat" to begin

### AI Provider Setup

#### Ollama (Local AI)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.2
ollama pull mistral

# Start Ollama service
ollama serve
```

#### OpenAI ChatGPT
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create API key
3. Add to `.env` file: `OPENAI_API_KEY=sk-...`

#### Google Gemini
1. Visit [makersuite.google.com](https://makersuite.google.com)
2. Generate API key
3. Add to `.env` file: `GEMINI_API_KEY=...`

### Interface Overview

#### Sidebar
- **New Chat Button**: Creates new conversation thread
- **Conversation List**: Shows recent chats with timestamps
- **Provider Settings**: Dropdown for AI provider selection
- **API Key Inputs**: Secure fields for API credentials
- **Model Selection**: Available models for chosen provider

#### Main Chat Area
- **Message Bubbles**: Color-coded for user/assistant
- **Real-time Updates**: Live message streaming
- **Auto-scroll**: Automatically scrolls to latest messages
- **Responsive Design**: Adapts to screen size

#### Input Area
- **Text Input**: Multi-line message composition
- **Send Button**: Circular button with arrow icon
- **Auto-resize**: Textarea expands with content
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line

## 🔧 Configuration Options

### Environment Variables
```bash
# Database Connection
YUGABYTE_HOST=your-host.com
YUGABYTE_PORT=5433
YUGABYTE_DB=chat_app
YUGABYTE_USER=your-username
YUGABYTE_PASSWORD=your-password

# AI Providers
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Application Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Application Settings
- **Theme**: Automatic dark/light mode detection
- **Font**: Inter font family for optimal readability
- **Animations**: Subtle transitions (can be disabled)
- **Cache**: Automatic caching for improved performance

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python test_db.py

# Check YugabyteDB status
curl http://localhost:7000/api/v1/version
```

### AI Provider Issues

#### Ollama Not Responding
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

#### API Key Problems
- **OpenAI**: Verify API key format (`sk-...`)
- **Gemini**: Check API key permissions
- **Rate Limits**: Monitor API usage quotas

### Performance Issues
- **Large Conversations**: Consider pagination for very long chats
- **Memory Usage**: Monitor system resources
- **Database Queries**: Check query performance with YugabyteDB metrics

### Common Errors
```
❌ Database not initialized → Run python test_db.py
❌ API key missing → Check .env file
❌ Model not found → Verify Ollama models installed
❌ Connection timeout → Check internet connectivity
```

## 🏗️ Project Structure

```
ai-chat-app/
├── UI.py                 # Main Streamlit application
├── database.py           # Database connection and operations
├── test_db.py           # Database testing and initialization
├── requirements.txt      # Python dependencies
├── README.md            # This documentation
├── .env                 # Environment variables (create)
└── .env.example         # Environment template
```

### Core Modules

#### UI.py
- **Main Application**: Streamlit-based web interface
- **State Management**: Session state handling
- **UI Components**: Chat interface, sidebar, input areas
- **Styling**: Custom CSS with Tailwind integration

#### database.py
- **Connection Management**: YugabyteDB connection handling
- **CRUD Operations**: Create, read, update, delete functions
- **Schema Management**: Database initialization and migrations
- **Query Optimization**: Efficient data retrieval

#### test_db.py
- **Database Testing**: Connection verification
- **Schema Validation**: Table creation and constraints
- **Data Integrity**: Test data operations
- **Performance Checks**: Query execution timing

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone repository
git clone https://github.com/your-username/ai-chat-app.git
cd ai-chat-app

# Create feature branch
git checkout -b feature/new-ai-provider

# Install development dependencies
pip install -r requirements-dev.txt
```

### Code Style
```bash
# Run linting
flake8 UI.py database.py

# Format code
black UI.py database.py

# Type checking
mypy UI.py database.py
```

### Adding New AI Providers
1. **Create Provider Function** in `UI.py`:
   ```python
   def chat_with_new_provider(model, messages):
       # Implementation
       pass
   ```

2. **Update Provider Dictionary**:
   ```python
   provider_icons["NewProvider"] = "🎯"
   ```

3. **Add to Sidebar Selection**:
   ```python
   ["Ollama", "ChatGPT", "Gemini", "NewProvider"]
   ```

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test database operations
python test_db.py
```

## 📄 API Documentation

### Database Functions

#### Connection Management
```python
get_db_connection() -> psycopg2.connection
# Returns database connection object
```

#### Conversation Operations
```python
create_conversation(title: str, provider: str, model: str) -> str
get_conversations(limit: int = 50) -> List[Dict]
get_conversation(conversation_id: str) -> Dict
update_conversation_title(conversation_id: str, title: str) -> bool
delete_conversation(conversation_id: str) -> bool
```

#### Message Operations
```python
save_message(conversation_id: str, role: str, content: str) -> str
get_messages(conversation_id: str) -> List[Dict]
generate_conversation_title(messages: List[Dict]) -> str
```

### AI Provider Functions
```python
chat_with_ollama(model: str, messages: List[Dict]) -> str
chat_with_openai(model: str, messages: List[Dict], api_key: str) -> str
chat_with_gemini(model: str, messages: List[Dict], api_key: str) -> str
```

## 🔒 Security Considerations

### API Key Management
- Store API keys in environment variables only
- Never commit API keys to version control
- Use `.env` files for local development
- Implement proper key rotation policies

### Database Security
- Use strong passwords for database access
- Implement connection pooling for production
- Enable SSL/TLS for database connections
- Regular security audits and updates

### Input Validation
- Sanitize user inputs to prevent injection attacks
- Validate message content and lengths
- Implement rate limiting for API calls
- Monitor for malicious usage patterns

## 📊 Performance Metrics

### Database Performance
- **Connection Pooling**: Efficient connection reuse
- **Query Optimization**: Indexed queries for fast retrieval
- **Data Compression**: Automatic data compression in YugabyteDB
- **Replication**: Built-in data replication and failover

### Application Performance
- **Lazy Loading**: Load conversations on demand
- **Caching**: Streamlit caching for expensive operations
- **Async Operations**: Non-blocking AI API calls
- **Memory Management**: Efficient session state handling

## 📈 Monitoring & Analytics

### Application Metrics
- **User Sessions**: Active conversation tracking
- **API Usage**: AI provider call statistics
- **Response Times**: Message generation performance
- **Error Rates**: Failure rate monitoring

### Database Metrics
- **Query Performance**: Execution time monitoring
- **Connection Health**: Database connectivity status
- **Storage Usage**: Data size and growth tracking
- **Backup Status**: Automated backup verification

## 🚀 Deployment Options

### Local Development
```bash
# Run locally
streamlit run UI.py --server.port 8501
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "UI.py", "--server.address", "0.0.0.0"]
```

### Cloud Deployment
- **Streamlit Cloud**: Direct deployment from GitHub
- **Heroku**: Container-based deployment
- **AWS/GCP**: Scalable cloud deployment
- **Docker Compose**: Multi-service orchestration

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit**: For the excellent web app framework
- **YugabyteDB**: For the robust distributed database
- **OpenAI**: For the ChatGPT API
- **Google**: For the Gemini AI platform
- **Ollama**: For local AI model support

## 📞 Support

### Getting Help
- **Documentation**: Check this README first
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join community discussions
- **Email**: Contact maintainers for support

### Community
- **GitHub**: Star and contribute to the project
- **Discord**: Join our community server
- **Twitter**: Follow for updates and announcements
- **Blog**: Read about new features and updates

---

**Made with ❤️ for AI enthusiasts and developers**

1. **Python 3.8+**
2. **Yugabyte Database** (running locally or remote)
3. **AI Provider Setup** (choose one or more):
   - Ollama (for local models)
   - OpenAI API key (for ChatGPT)
   - Google Gemini API key (for Gemini)

## Installation

1. **Clone or download the files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Yugabyte Database:**
   - Install YugabyteDB (see https://docs.yugabyte.com/preview/quick-start/)
   - Create a database named `chat_app` (or update the connection settings)
   - The application will automatically create the required tables on first run

4. **Database Configuration** (already configured for your YugabyteDB Cloud instance):
   - Host: `us-east-1.caf91660-4797-4dec-91fd-a282ebb4037b.aws.yugabyte.cloud`
   - Port: `5433`
   - Database: `yugabyte`
   - Username: `admin`
   - Password: `cXgvtpIzCjd2yfjoTW-ed8TFhqP3qi`

   **Optional**: Override with environment variables if needed:
   ```bash
   export YUGABYTE_HOST=your_custom_host
   export YUGABYTE_PORT=5433
   export YUGABYTE_DB=your_database
   export YUGABYTE_USER=your_username
   export YUGABYTE_PASSWORD=your_password

   # AI Providers
   export OPENAI_API_KEY=your_openai_key_here
   export GEMINI_API_KEY=your_gemini_key_here
   ```

## Running the Application

```bash
streamlit run UI.py
```

The application will open in your default web browser at `http://localhost:8501`

## Usage

### Starting a New Conversation
1. Click the "➕ New Chat" button in the sidebar
2. Select your preferred AI provider and model
3. Start chatting!

### Switching Between Conversations
- View your recent conversations in the sidebar
- Click on any conversation to switch to it
- Active conversation is marked with a green dot (🟢)

### Managing Conversations
- **Delete**: Click the trash icon (🗑️) next to any conversation
- **Clear Current Chat**: Use the "Clear Current Chat" button to remove all messages from the current conversation

## Database Schema

The application creates two main tables:

### `conversations`
- `id`: UUID primary key
- `title`: Auto-generated title from first message
- `provider`: AI provider (Ollama/ChatGPT/Gemini)
- `model`: Specific model used
- `created_at`: Timestamp
- `updated_at`: Last modified timestamp

### `messages`
- `id`: UUID primary key
- `conversation_id`: Foreign key to conversations
- `role`: 'user' or 'assistant'
- `content`: Message text
- `created_at`: Timestamp

## Accessibility Features

- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: ARIA labels and semantic HTML
- **High Contrast Mode**: Automatic support for high contrast preferences
- **Reduced Motion**: Respects user's motion preferences
- **Focus Indicators**: Clear focus outlines for keyboard users
- **Semantic HTML**: Proper roles and landmarks for assistive technologies

## Troubleshooting

### Database Connection Issues
- Ensure YugabyteDB is running
- Check connection settings in `database.py`
- Verify database credentials

### AI Provider Issues
- **Ollama**: Make sure Ollama is installed and running (`ollama serve`)
- **OpenAI**: Verify your API key is set and has credits
- **Gemini**: Check your Gemini API key

### Performance Issues
- For large conversations, consider using smaller models
- Database queries are optimized with proper indexing

## Security Notes

- API keys are stored in environment variables (never in code)
- Database passwords should be properly secured
- The application includes basic error handling and input validation

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source. Please check individual component licenses for details.
