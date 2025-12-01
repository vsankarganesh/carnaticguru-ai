# CarnaticGuru AI - Agent Connection & Persistent Memory Guide

## ✅ YES - Agents ARE Connected to UI with Persistent Memory

When you run `./manage.sh start-all`, here's exactly how everything connects:

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UI Dashboard                                  │
│                    (http://localhost:8002)                            │
│  - User Selection (Arjun, Priya, Rohan, Admin)                      │
│  - Learning Categories (Lessons, Swara Patterns, Raga Info)         │
│  - Chat Interface                                                     │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ POST /api/query
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ui_app.py (Port 8002)                            │
│                   FastAPI Backend Runner                              │
│                                                                        │
│  1. Receives: {user_id, query, category}                            │
│  2. Creates/Gets Session from DatabaseSessionService                │
│  3. Calls: runner.run_async(orchestrator_agent)                     │
│  4. Returns: Response with timestamp                                │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ Uses google.adk.runners.Runner
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Google ADK Runner + Orchestrator Agent                  │
│         (carnatic_guru/orchestrator_agent/agent.py)                 │
│                                                                        │
│  Routing Logic:                                                       │
│  - "lessons" → routes to lesson_agent                               │
│  - "swara" → routes to pattern_agent                                │
│  - "raga" → routes to raga_agent                                    │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      │ DatabaseSessionService stores all events
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Persistent SQLite Database                               │
│              (carnatic_guru.db)                                       │
│                                                                        │
│  Tables:                                                              │
│  - sessions: {app_name, user_id, session_id, events, state}         │
│  - Shared across: UI, CLI runners, web_app.py, etc.                │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Component: Runner File

**File: `ui_app.py` (Lines 180-260)**

This is the **main runner** that connects everything:

```python
@app.post("/api/query")
async def run_query(request: QueryRequest):
    """Process query through orchestrator agent"""
    
    # 1. Get/Create session from persistent database
    session = await session_service.get_session(
        app_name=app_instance.name,
        user_id=request.user_id,
        session_id=session_id,
    )
    
    # 2. Run orchestrator agent through Runner
    async for event in runner.run_async(
        user_id=request.user_id,
        session_id=session_id,
        new_message=content,
    ):
        events.append(event)
        # Extract response as events arrive
    
    # 3. Persist to database automatically via session_service
    return QueryResponse(response=response_text, ...)
```

## Flow When You Ask a Question in UI

**Step-by-step what happens:**

1. **User selects**: Arjun + "🎼 Raga Information"
2. **User types**: "Tell me about Kalyani raga"
3. **Frontend sends**: `POST /api/query` with `{user_id: "learner_1", query: "Tell me about Kalyani raga", category: "raga_info"}`
4. **Backend (ui_app.py)**:
   - Gets session: `learner_1_session` from `carnatic_guru.db`
   - If new user, creates fresh session with empty history
   - Creates message content with category context: `"[raga_info] Tell me about Kalyani raga"`
5. **Runner executes orchestrator_agent**:
   - Orchestrator receives: `"[raga_info] Tell me about Kalyani raga"`
   - Routes to: `raga_agent` (because of `raga_info` prefix)
   - raga_agent generates response about Kalyani raga
6. **DatabaseSessionService stores**:
   - User message: "Tell me about Kalyani raga" (role: user)
   - Agent response: Description of Kalyani raga (role: model)
   - Timestamp: 2024-12-19T15:45:32.123Z
7. **Response sent to UI**: 
   - User sees: "Description of Kalyani raga..."
   - Timestamp shown in chat
8. **Session history updated**: 
   - User can see past interactions in sidebar
   - Persists across page reloads & restarts

## Persistent Memory Details

### Session Storage
- **Location**: `carnatic_guru.db` (SQLite)
- **Session Key**: `{app_name}:{user_id}:{session_id}`
- **Example**: `CarnaticGuru:learner_1:learner_1_session`

### What Gets Stored
Each conversation event includes:
```json
{
  "author": "user" | "model",
  "content": {
    "parts": [{"text": "..."}]
  },
  "timestamp": "ISO-8601 timestamp",
  "metadata": {...}
}
```

### Who Can Access
✅ **UI** (ui_app.py) - Full access
✅ **CLI Runners** (runner_persistent.py, orchestrator_persistent.py) - Full access
✅ **Web API** (web_app.py) - Full access via DatabaseSessionService
✅ **Session Loader** (load_session.py) - Query historical data

### Persistence Guarantee
- **Survives UI reload**: ✅ Session recreated from database
- **Survives app restart**: ✅ DatabaseSessionService reconnects to carnatic_guru.db
- **Shared across interfaces**: ✅ All use same DatabaseSessionService instance
- **User isolation**: ✅ Each user_id has separate session

## Startup Process (`./manage.sh start-all`)

```bash
1. Kill existing processes on ports 8001, 8002
   └─ Ensures clean start

2. Start UI Server (ui_app.py)
   └─ Port 8002
   └─ Initializes: DatabaseSessionService → carnatic_guru.db
   └─ Initializes: Runner instance
   └─ Loads: orchestrator_agent

3. Start Web API (web_app.py)
   └─ Port 8001
   └─ Alternative access to same services
   └─ Also uses DatabaseSessionService

4. Logs available at:
   └─ /tmp/carnatic_gui_ui.log
   └─ /tmp/carnatic_gui_api.log
```

## Testing Persistent Memory

### Option 1: Via UI
1. Run: `./manage.sh start-all`
2. Open: http://localhost:8002
3. Select user: Arjun
4. Select category: Lessons
5. Ask: "What is sargam?"
6. Reload page (Cmd+R)
7. **Result**: History remains in sidebar ✅

### Option 2: Via CLI
```bash
# After UI is running, check session in database:
python load_session.py learner_1

# Output shows all events from learner_1_session
```

### Option 3: Via Terminal
```bash
# Check database directly
sqlite3 carnatic_guru.db "SELECT * FROM sessions WHERE user_id='learner_1';"
```

## Architecture Decisions

| Component | Choice | Why |
|-----------|--------|-----|
| **Runner** | google.adk.runners.Runner | Official SDK, handles orchestrator + agents |
| **Session Store** | SQLite + DatabaseSessionService | Persistent, async-compatible, no external DB needed |
| **UI Framework** | FastAPI + HTML/CSS/JS | No build tools, simple deployment |
| **Memory Service** | InMemoryMemoryService | Works with DatabaseSessionService |
| **Artifact Service** | InMemoryArtifactService | Sufficient for text-based learning |

## Key Files Reference

| File | Purpose | Role |
|------|---------|------|
| **ui_app.py** | Web UI + Backend | Main runner (ports 8002) |
| **runner_persistent.py** | CLI runner with DB | Alternative CLI access |
| **orchestrator_persistent.py** | CLI with routing | Alternative CLI access |
| **web_app.py** | REST API | Alternative web access (port 8001) |
| **carnatic_guru/orchestrator_agent/agent.py** | Routing logic | Routes to lesson/pattern/raga agents |
| **carnatic_guru.db** | SQLite database | Persistent session storage |

## Verification Checklist

After running `./manage.sh start-all`:

- [ ] UI loads at http://localhost:8002
- [ ] All 4 users selectable
- [ ] Can select learning categories
- [ ] Queries processed (6-8 seconds typical)
- [ ] Responses appear in chat
- [ ] Session history shows in sidebar
- [ ] Can reload page → history persists
- [ ] Database file: `carnatic_guru.db` exists and grows
- [ ] Logs available: `/tmp/carnatic_gui_*.log`

## Troubleshooting

**Q: "Session not found" error**
- A: DatabaseSessionService creates session automatically on first query

**Q: Memory lost after reload**
- A: Check `/tmp/carnatic_gui_ui.log` for database connection errors

**Q: Port 8002 already in use**
- A: Run `./manage.sh stop-all` first, or manually: `lsof -ti:8002 | xargs kill -9`

**Q: Queries slow (>15 seconds)**
- A: Gemini 2.0-Flash-Lite model may be rate-limited. Check: `grep "Rate limit" /tmp/carnatic_gui_*.log`

---

## Summary

**Q: When I start with `./manage.sh start-all`, are agents connected to UI with persistent memory?**

**A:** ✅ **YES - 100% connected with persistent memory**

- Runner: **ui_app.py** (main)
- Database: **carnatic_guru.db** (SQLite, persistent)
- Orchestrator: Fully integrated and routing queries
- Memory: All conversations saved and survive restarts
- Users: 4 profiles with separate sessions
- Access: UI, CLI runners, and REST API all share same database

**To start:** `./manage.sh start-all`  
**To access:** http://localhost:8002
