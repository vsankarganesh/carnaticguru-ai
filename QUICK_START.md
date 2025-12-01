# 🎵 CarnaticGuru - Quick Reference Card

## ONE-LINE STARTS

```bash
# Start everything (recommended)
./manage.sh start-all

# Start UI only
./manage.sh start-ui

# Stop everything
./manage.sh stop-all
```

## SERVICE DASHBOARD

| Service | Port | URL | Command |
|---------|------|-----|---------|
| **UI Dashboard** | 8002 | http://localhost:8002 | `./manage.sh start-ui` |
| **Web API** | 8001 | http://localhost:8001 | `./manage.sh start-api` |
| **Status** | - | - | `./manage.sh status` |

## ESSENTIAL COMMANDS

```bash
# STARTING
./manage.sh start-ui              # ← UI (most common)
./manage.sh start-api             # ← REST API
./manage.sh start-all             # ← Both services
./manage.sh start-cli             # ← Interactive CLI

# STOPPING
./manage.sh stop-ui               # ← Stop UI
./manage.sh stop-api              # ← Stop API
./manage.sh stop-all              # ← Stop all

# CHECKING
./manage.sh status                # ← See what's running
./manage.sh logs-ui               # ← UI server logs
./manage.sh logs-api              # ← API server logs
./manage.sh test                  # ← Run tests

# HELP
./manage.sh help                  # ← Show all commands
```

## MANUAL COMMANDS (if needed)

```bash
# Activate environment
source .venv/bin/activate

# Start UI manually
python ui_app.py

# Start API manually
python web_app.py

# Start CLI
python orchestrator_persistent.py

# Force kill UI
lsof -ti:8002 | xargs kill -9

# Force kill API
lsof -ti:8001 | xargs kill -9

# Check what's on port 8002
lsof -i :8002
```

## TYPICAL WORKFLOW

```bash
# 1. Navigate to project
cd /Users/vsankarganesh/projects/carnaticguru-ai

# 2. Start services
./manage.sh start-all

# 3. Open browser
open http://localhost:8002

# 4. Use the app
# - Select a user
# - Choose learning category
# - Ask questions
# - View history

# 5. Stop when done
./manage.sh stop-all
```

## TROUBLESHOOTING QUICK FIXES

```bash
# Port already in use? Script handles it automatically
./manage.sh start-ui

# Services not responding?
./manage.sh stop-all && sleep 2 && ./manage.sh start-all

# Check all services
./manage.sh status

# Database issues? (will recreate on next start)
rm carnatic_guru.db && ./manage.sh start-ui

# Need logs?
./manage.sh logs-ui
./manage.sh logs-api
```

## FILE LOCATIONS

```bash
# Project root
/Users/vsankarganesh/projects/carnaticguru-ai/

# Database
carnatic_guru.db

# Configuration files
manage.sh              # ← Control script
ui_app.py             # ← UI server
web_app.py            # ← API server
requirements.txt      # ← Dependencies

# Documentation
UI_README.md          # ← UI features
STARTUP_GUIDE.md      # ← Detailed startup guide
```

## URLS

```
UI Dashboard:    http://localhost:8002
Web API:         http://localhost:8001
Database:        carnatic_guru.db (SQLite)
```

## DEFAULT USERS

```
👨‍🎓 Arjun (learner_1)
👩‍🎓 Priya (learner_2)
👨‍🎓 Rohan (learner_3)
👨‍💼 Admin (admin)
```

## LEARNING OPTIONS

```
📚 Lessons          → Learn fundamentals
🎵 Swara Patterns   → Practice patterns
🎼 Raga Information → Learn about ragas
```

## QUICK TEST

```bash
# After starting UI, test it works:
curl http://localhost:8002/api/users
# Should return list of users

# Test a query:
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{"user_id":"learner_1","query":"Tell me about Kalyani","category":"raga_info"}'
```

## ENVIRONMENT SETUP (First time only)

```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## KEYBOARD SHORTCUTS

| Action | Key |
|--------|-----|
| Send message | Enter |
| Focus search | Ctrl+K (on some browsers) |

## COMMON ERRORS & FIXES

| Error | Fix |
|-------|-----|
| Port 8002 in use | `./manage.sh start-ui` (auto-handles) |
| Module not found | `pip install -r requirements.txt` |
| Database locked | `./manage.sh stop-all && rm carnatic_guru.db` |
| Venv not activated | `source .venv/bin/activate` |

---

**START HERE:** `./manage.sh start-all` then open http://localhost:8002

**Questions?** See STARTUP_GUIDE.md for detailed documentation
