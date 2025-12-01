# CarnaticGuru AI 🎵

An intelligent AI-powered platform for learning Carnatic music, using Google's ADK (Agent Development Kit) to deliver structured lessons with detailed exercises and notations.

## 🎯 Problem Statement

Learning Carnatic music requires access to:
- **Structured lessons** with proper notation
- **Exercise progressions** (Sarali Varisai → Janta Varisai → Taatu → etc.)
- **Raag information** with arohanam/avarohanam
- **Swara patterns** for practice
- **Personalized guidance** based on learning level

Traditional platforms often:
- ❌ Return summarized/incomplete lesson content
- ❌ Don't preserve notation formatting
- ❌ Lack integration between multiple learning resources
- ❌ Can't adapt to different user skill levels

## ✅ Solution

CarnaticGuru AI solves this by:

1. **Multi-Agent Orchestration** - Orchestrator agent routes queries to specialized agents
2. **PDF-Based Lessons** - Extracts complete lesson content from carnatic_basics.pdf
3. **Tool-Based Architecture** - Uses MCP (Model Context Protocol) tools for reliable data access
4. **Centralized Configuration** - Single point to change LLM models globally
5. **Clean UI** - FastAPI dashboard with dark theme and user management
6. **Persistent Sessions** - SQLite database for user progress tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Interface (FastAPI + Dark Theme)       │
│          http://localhost:8002                      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Orchestrator Agent    │
        │  (routing layer)       │
        └────────────┬───────────┘
                     │
        ┌────────────▼──────────────┐
        │   read_pdf_lesson tool    │
        │   (MCP interface)         │
        └────────────┬──────────────┘
                     │
        ┌────────────▼──────────────────────┐
        │  PDF Lesson Reader                │
        │  carnatic_basics.pdf (41 pages)   │
        │  - Sarali Varisai (Lesson 1)      │
        │  - Janta Varisai (Lesson 2)       │
        │  - Taatu Varisai (Lesson 3)       │
        │  - Melakarti & Janya Ragas        │
        └───────────────────────────────────┘

Database Layer:
┌─────────────────────────────────────┐
│  SQLite (carnatic_guru.db)          │
│  - Users table                      │
│  - Session history                  │
└─────────────────────────────────────┘
```

## 📋 Key Features

### 1. **Orchestrator Agent**
- Main routing layer that processes all user queries
- Routes to appropriate specialized agents
- Returns unmodified content (no markdown formatting)
- Handles user intent understanding

### 2. **Basic Lesson Agent**
- Fetches lesson content from PDF via `read_pdf_lesson` tool
- Returns complete exercises with all notations
- Preserves exact PDF formatting

### 3. **MCP PDF Server**
- `read_pdf_lesson(query)` - Searches and retrieves lesson content
- `get_available_lessons()` - Lists all available lessons
- Smart search that skips table of contents
- Returns up to 2000 characters of lesson content

### 4. **Centralized Configuration**
- Single `carnatic_guru/config.py` file
- Change model globally: `DEFAULT_MODEL = "gemini-2.0-flash-lite"`
- All agents automatically use new model
- Agent instructions centralized

### 5. **UI Dashboard**
- Dark theme by default
- User selection dropdown (Arjun, Priya, Kavya)
- Full-width chat interface
- Real-time response streaming
- Session history tracking

### 6. **Database Integration**
- SQLite user management
- Session persistence
- Learning progress tracking
- User avatars and metadata

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Google API Key (Gemini API)
- macOS/Linux terminal

### Setup

1. **Clone and enter directory**
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
```

2. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_api_key_here
EOF
```

5. **Initialize database** (if needed)
```bash
python3 init_db.py
```

6. **Start all services**
```bash
bash manage.sh start-all
```

Services will be available at:
- 🎵 **UI Dashboard**: http://localhost:8002
- 🌐 **Web API**: http://localhost:8001

### Usage

#### Web UI
1. Open http://localhost:8002
2. Select a user from dropdown (top-right)
3. Type your query about Carnatic lessons
4. Example queries:
   - "sarali varisai"
   - "janta varisai exercise 2"
   - "taatu"
   - "melakartha ragas"

#### API Endpoint
```bash
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "learner_1",
    "query": "janta varisai"
  }'
```

#### Response Example
```
janTai varisai (lesson 2)
raagam: maayamaaLava gowLa
15th mElakartha
aarOhaNam: S R1 G3 M1 P D1 N3 S
avarOhaNam: S N3 D1 P M1 G3 R1 S
taaLam: aadi

1.
s   s   r   r   |   g   g   |   m   m   ||
p   p   d   d   |   n   n   |   S   S   ||

2.
s   s   r   r   |   g   g   |   m   m   ||
r   r   g   g   |   m   m   |   p   p   ||
...
```

## 📁 Project Structure

```
carnaticguru-ai/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── manage.sh                          # Service management script
├── .env                               # Environment variables (not in repo)
│
├── carnatic_guru/
│   ├── config.py                      # Centralized configuration
│   ├── mcp_pdf_server.py              # PDF extraction tools
│   ├── __init__.py
│   │
│   ├── orchestrator_agent/
│   │   ├── agent.py                   # Orchestrator (routing layer)
│   │   └── __init__.py
│   │
│   └── basic_lesson_agent/
│       ├── agent.py                   # Lesson delivery agent
│       └── __init__.py
│
├── ui_app.py                          # FastAPI UI application (port 8002)
├── web_app.py                         # Web API application (port 8001)
├── carnatic_basics.pdf                # PDF with 41 pages of lessons
├── carnatic_guru.db                   # SQLite database (auto-created)
│
├── orchestrator_runner.py             # Test runner for orchestrator
├── init_db.py                         # Database initialization
└── basic_lesson_agent.py              # Root-level wrapper for adk run
```

## 🔧 Configuration

### Change LLM Model

Edit `carnatic_guru/config.py`:
```python
# Change this line to switch models globally
DEFAULT_MODEL = "gemini-2.0-flash"  # or "gemini-1.5-pro", etc.
```

All agents will automatically use the new model.

### Add New Users

Edit `carnatic_guru/config.py` or use SQLite directly:
```python
# In init_db.py or database
INSERT INTO users (id, name, avatar, color) 
VALUES ('learner_4', 'Ravi', '🎸', '#FF6B6B');
```

### Modify Agent Instructions

Edit `carnatic_guru/config.py`:
```python
ORCHESTRATOR_AGENT_INSTRUCTION = """Your custom instruction here"""
BASIC_LESSON_AGENT_INSTRUCTION = """Your custom instruction here"""
```

## 📊 Available Lessons

From `carnatic_basics.pdf`:

1. **Sarali Varisai** (Lesson 1) - Pages 4-11
   - Raagam: Maayamaalava gowLa
   - 3 exercises with full notations

2. **Janta Varisai** (Lesson 2) - Pages 12-23
   - Raagam: Maayamaalava gowLa
   - 10+ exercises

3. **Taatu Varisai** (Lesson 3) - Pages 24-27
   - Advanced progression

4. **Melakarti Ragas** (Lesson 4-5)
   - Classification and arohanam/avarohanam

5. **Alankaarams** (Lesson 6)
   - Ornamental phrases and patterns

## 🛠️ Service Management

```bash
# Start all services
bash manage.sh start-all

# Stop all services
bash manage.sh stop-all

# Restart all services
bash manage.sh restart-all

# Check service status
lsof -i :8002  # UI
lsof -i :8001  # API
```

## 📝 API Reference

### Query Endpoint

**POST** `/api/query`

Request:
```json
{
  "user_id": "learner_1",
  "query": "janta varisai exercise 2",
  "category": "General"
}
```

Response:
```json
{
  "response": "lesson content here...",
  "user_name": "Arjun",
  "category": "General",
  "timestamp": "2025-11-28T11:50:59.056824"
}
```

### Session Endpoint

**GET** `/api/session/{user_id}`

Returns session history and all previous queries.

### Users Endpoint

**GET** `/api/users`

Returns list of all available users.

## 🧪 Testing

### Test Individual Agents

```bash
# Test orchestrator agent
python3 -c "
from carnatic_guru.orchestrator_agent.agent import orchestrator_agent
print(f'✓ Orchestrator: {orchestrator_agent.name}')
"

# Test config system
python3 -c "
from carnatic_guru.config import DEFAULT_MODEL
print(f'✓ Model: {DEFAULT_MODEL}')
"
```

### Test PDF Extraction

```bash
python3 -c "
from carnatic_guru.mcp_pdf_server import read_pdf_lesson
result = read_pdf_lesson('sarali')
print(result[:500])
"
```

### Test Full Query

```bash
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "learner_1", "query": "sarali varisai"}'
```

## 📚 Learning Path

Recommended progression for students:

1. **Start** → Sarali Varisai (basic scales)
2. **Progress** → Janta Varisai (double patterns)
3. **Advance** → Taatu Varisai (complex patterns)
4. **Specialize** → Melakarti ragas and janya ragas
5. **Master** → Alankaarams and compositions

## 🔐 Environment Variables

Required in `.env`:
```
GOOGLE_API_KEY=your_api_key_here
```

Optional:
```
LOG_LEVEL=INFO
DB_PATH=carnatic_guru.db
PDF_PATH=carnatic_basics.pdf
```

## 🐛 Troubleshooting

### Import Error: "No module named 'carnatic_guru'"
```bash
# Ensure you're in the project root
cd /Users/vsankarganesh/projects/carnaticguru-ai
# And running from there
```

### API returning 429 RESOURCE_EXHAUSTED
- You've exceeded the Gemini free tier quota (200 requests/day)
- Wait until next day or upgrade to paid plan
- Check usage at: https://ai.google.dev/usage

### PDF not found
```bash
# Ensure carnatic_basics.pdf exists in project root
ls -la carnatic_basics.pdf
```

### Database locked
```bash
# Remove stale database and reinitialize
rm carnatic_guru.db
python3 init_db.py
```

## 📖 Documentation

- [QUICK_START.md](QUICK_START.md) - Quick setup guide
- [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Detailed startup instructions
- [AGENT_CONNECTION_GUIDE.md](AGENT_CONNECTION_GUIDE.md) - Agent architecture details
- [observability_implementation.md](observability_implementation.md) - Logging and monitoring

## 🤝 Contributing

To extend CarnaticGuru AI:

1. **Add new lessons** - Add PDF pages and update search logic
2. **Add new agents** - Create in `carnatic_guru/new_agent/agent.py`
3. **Modify UI** - Edit HTML/CSS in `ui_app.py`
4. **Change model** - Update `DEFAULT_MODEL` in `config.py`

## 📦 Dependencies

- **google-adk** - Agent Development Kit for building AI agents
- **fastapi** - Web framework for UI and API
- **uvicorn** - ASGI server
- **pypdf** - PDF text extraction
- **sqlalchemy** - Database ORM
- **aiosqlite** - Async SQLite driver
- **python-dotenv** - Environment variable loading

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `tail -f /tmp/ui.log`
3. Check API: http://localhost:8001 (when running)
4. See [Documentation](#documentation)

## 📄 License

This project uses Carnatic music materials from karnatik.com
Ensure compliance with source material usage terms.

## 🙏 Acknowledgments

- Carnatic music lesson materials from karnatik.com
- Google ADK for agent development capabilities
- Gemini API for language understanding

## 🎓 Educational Use

CarnaticGuru AI is designed for:
- ✅ Music students learning Carnatic basics
- ✅ Teachers seeking structured lesson delivery
- ✅ Researchers studying AI in music education
- ✅ Developers learning agent-based systems

---

**Happy Learning! 🎵🎸🎹**

For the latest updates, visit: https://github.com/vsankarganesh/carnaticguru-ai
