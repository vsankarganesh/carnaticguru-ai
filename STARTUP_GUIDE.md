# 🎵 CarnaticGuru AI - Startup & Shutdown Guide

## Quick Start (30 seconds)

### Start Everything
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
./manage.sh start-all
```

Then open: **http://localhost:8002**

### Stop Everything
```bash
./manage.sh stop-all

```
### Restart Everything
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
./manage.sh restart-all
```
---

# Watch UI logs in real-time
tail -f /tmp/ui.log

# Watch Web API logs
tail -f /tmp/web_api.log

## 📖 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Commands](#quick-commands)
3. [Detailed Instructions](#detailed-instructions)
4. [Multiple Servers](#running-multiple-servers)
5. [Troubleshooting](#troubleshooting)
6. [Service Ports](#service-ports)

---

## Prerequisites

### Setup (First Time Only)

```bash
# Navigate to project
cd /Users/vsankarganesh/projects/carnaticguru-ai

# Create virtual environment (if not exists)
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Check Setup
```bash
# Verify venv is active
which python  # Should show .venv path

# Verify dependencies
python -c "import google.adk; print('✓ google-adk installed')"
```

---

## Quick Commands

Use the `manage.sh` script for easy control:

### Start Services
```bash
# Start UI only
./manage.sh start-ui

# Start Web API only
./manage.sh start-api

# Start both together
./manage.sh start-all

# Restart both together
./manage.sh restart-all

# Start Orchestrator CLI (interactive)
./manage.sh start-cli

# Start Persistent CLI
./manage.sh start-persistent
```

### Stop Services
```bash
# Stop UI
./manage.sh stop-ui

# Stop Web API
./manage.sh stop-api

# Stop all services
./manage.sh stop-all
```

### Check Status
```bash
# See what's running
./manage.sh status

# View UI logs
./manage.sh logs-ui

# View API logs
./manage.sh logs-api

# Run tests
./manage.sh test
```

---

## Detailed Instructions

### Method 1: Using Management Script (RECOMMENDED)

#### Start UI Server
```bash
./manage.sh start-ui
```
- Starts on port 8002
- Opens at http://localhost:8002
- All features enabled: Users, Categories, Chat

#### Start Web API
```bash
./manage.sh start-api
```
- Starts on port 8001
- REST API endpoints for programmatic access

#### Start Both
```bash
./manage.sh start-all
```
- Starts UI (port 8002) + Web API (port 8001)
- Both fully functional

#### Stop Services
```bash
./manage.sh stop-ui       # Stop just UI
./manage.sh stop-api      # Stop just API
./manage.sh stop-all      # Stop everything
```

---

### Method 2: Manual Python Commands

#### Start UI Manually
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
source .venv/bin/activate
python ui_app.py
```

#### Start Web API Manually
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
source .venv/bin/activate
python web_app.py
```

#### Start Orchestrator CLI
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
source .venv/bin/activate
python orchestrator_persistent.py
```

#### Kill Services Manually
```bash
# Kill by port
lsof -ti:8002 | xargs kill -9  # Kill UI
lsof -ti:8001 | xargs kill -9  # Kill API

# Kill by process name
pkill -f "python ui_app.py"
pkill -f "python web_app.py"
```

---

### Method 3: Background Execution

#### Start and keep running in background
```bash
cd /Users/vsankarganesh/projects/carnaticguru-ai
source .venv/bin/activate
nohup python ui_app.py > ui.log 2>&1 &
```

#### Check if running
```bash
ps aux | grep ui_app.py | grep -v grep
```

#### Stop background process
```bash
pkill -f "python ui_app.py"
```

---

## Running Multiple Servers

### Scenario: Run all 4 servers simultaneously

```bash
# Terminal 1: UI Server
./manage.sh start-ui

# Terminal 2: Web API
./manage.sh start-api

# Terminal 3: Orchestrator CLI (interactive)
./manage.sh start-cli

# Terminal 4: Persistent CLI
./manage.sh start-persistent
```

### Access Points
- **UI Dashboard**: http://localhost:8002
- **Web API**: http://localhost:8001
- **CLI Servers**: Terminal input/output

---

## Service Ports & URLs

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **UI Dashboard** | 8002 | http://localhost:8002 | Modern web interface |
| **Web API** | 8001 | http://localhost:8001 | REST API endpoints |
| **Database** | N/A | carnatic_guru.db | SQLite session storage |

---

## Service Details

### 🎵 UI Server (Port 8002)

**What it does:**
- Modern web interface for learning
- User selection (4 dummy profiles)
- Learning categories (Lessons, Patterns, Ragas)
- Chat interface with AI responses
- Session history tracking

**Start:**
```bash
./manage.sh start-ui
```

**Access:**
```
http://localhost:8002
```

**Features:**
- ✅ User profiles: Arjun, Priya, Rohan, Admin
- ✅ 3 learning categories with routing
- ✅ Persistent session storage
- ✅ Real-time chat responses
- ✅ Session history display

---

### 🌐 Web API (Port 8001)

**What it does:**
- REST API for programmatic access
- JSON request/response format
- Session management endpoints

**Start:**
```bash
./manage.sh start-api
```

**Access:**
```
http://localhost:8001
```

**Endpoints:**
- `POST /query` - Submit query
- `GET /session/{id}` - Get session history
- `GET /health` - Health check

---

### 🎼 Orchestrator CLI

**What it does:**
- Interactive command-line interface
- Orchestrator agent with routing
- Persistent session storage
- Session history with `history` command

**Start:**
```bash
./manage.sh start-cli
```

**Usage:**
```
> Tell me about Kalyani raga
Orchestrator routes to Raga Agent...
> history
Shows session events
> exit
Quits
```

---

### 📚 Persistent CLI Runner

**What it does:**
- Python script interface
- Direct agent interaction
- Test queries with persistence

**Start:**
```bash
./manage.sh start-persistent
```

---

## Startup Workflows

### Workflow 1: UI Only (Most Common)
```bash
./manage.sh start-ui
# Open http://localhost:8002
# Use the web interface
./manage.sh stop-ui
```

### Workflow 2: Development Mode
```bash
# Terminal 1: Start UI with logs
python ui_app.py

# Terminal 2: Run tests while UI is running
python test_orchestrator_ui.py

# When done:
pkill -f "python ui_app.py"
```

### Workflow 3: Full Stack
```bash
./manage.sh start-all
# Both UI and API running
# Use whichever interface you need
./manage.sh stop-all
```

### Workflow 4: API Only (Integration)
```bash
./manage.sh start-api
# Use http://localhost:8001 for programmatic access
./manage.sh stop-api
```

---

## Status Monitoring

### Check All Services
```bash
./manage.sh status
```

Output shows:
- Port 8002 status (UI)
- Port 8001 status (API)
- Python processes running
- Process IDs (PIDs)

### Check Specific Port
```bash
# Is UI running?
lsof -i :8002

# Is API running?
lsof -i :8001

# Show details
netstat -an | grep LISTEN | grep 800
```

### View Logs
```bash
# UI logs
./manage.sh logs-ui

# API logs
./manage.sh logs-api

# Follow in real-time
tail -f /tmp/ui.log
tail -f /tmp/web_api.log
```

---

## Troubleshooting

### Problem: "Address already in use" on port 8002

**Solution:**
```bash
# Option 1: Use management script (auto-handles this)
./manage.sh start-ui

# Option 2: Manual kill
lsof -ti:8002 | xargs kill -9
sleep 1
python ui_app.py

# Option 3: Find and stop process
ps aux | grep ui_app.py
kill -9 <PID>
```

### Problem: Virtual environment not activated

**Solution:**
```bash
source .venv/bin/activate

# Verify activation
which python  # Should show .venv path
```

### Problem: Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt

# Verify key packages
python -c "import google.adk; import fastapi; print('✓ All OK')"
```

### Problem: Database locked

**Solution:**
```bash
# Stop all services
./manage.sh stop-all
sleep 2

# Start fresh
./manage.sh start-ui

# If still locked, delete DB (will be recreated)
rm carnatic_guru.db
./manage.sh start-ui
```

### Problem: Services not responding

**Solution:**
```bash
# Check status
./manage.sh status

# Restart services
./manage.sh stop-all
sleep 3
./manage.sh start-ui

# Check health
curl http://localhost:8002/api/users
```

### Problem: Port 8002 shows as STOPPED but can't start

**Solution:**
```bash
# Force kill anything on port 8002
sudo lsof -ti:8002 | xargs sudo kill -9

# Clear system resources
sleep 5

# Start fresh
./manage.sh start-ui
```

---

## Performance Tips

### Optimize Startup
```bash
# Pre-load venv in background
./manage.sh start-ui &

# Parallel start
./manage.sh start-ui &
./manage.sh start-api &
```

### Monitor Performance
```bash
# Watch resource usage while running
watch -n 1 'ps aux | grep python'

# Check memory
ps aux | grep ui_app | awk '{print $6}'  # Memory in KB
```

### Cleanup
```bash
# Regular cleanup
./manage.sh stop-all

# Clear unused processes
pkill -f "python.*\.py"  # Kill ALL Python scripts

# Reset database if needed
rm carnatic_guru.db
./manage.sh start-ui
```

---

## Advanced Usage

### Custom Port
```bash
# UI on different port (requires code edit)
# Edit ui_app.py, line: uvicorn.run(..., port=9000, ...)

# Or use environment variable approach:
export UI_PORT=9000
python ui_app.py
```

### Headless Mode
```bash
# Start and disown (background)
./manage.sh start-all &
disown
# Services run even if terminal closes
```

### SSH/Remote Deployment
```bash
# SSH to server
ssh user@server

# Start services
cd /path/to/carnaticguru-ai
./manage.sh start-all

# Access from local machine
http://server-ip:8002
```

---

## Daemon/Service Installation (Optional)

### Create systemd service (Linux)

Create `/etc/systemd/system/carnaticguru.service`:
```ini
[Unit]
Description=CarnaticGuru AI UI Service
After=network.target

[Service]
Type=simple
User=vsankarganesh
WorkingDirectory=/Users/vsankarganesh/projects/carnaticguru-ai
ExecStart=/bin/bash -c 'source .venv/bin/activate && python ui_app.py'
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl start carnaticguru
sudo systemctl enable carnaticguru
sudo systemctl status carnaticguru
```

---

## Cheat Sheet

```bash
# Quick start
./manage.sh start-all

# Check status
./manage.sh status

# Stop everything
./manage.sh stop-all

# UI only
./manage.sh start-ui

# API only
./manage.sh start-api

# Interactive CLI
./manage.sh start-cli

# View logs
./manage.sh logs-ui

# Run tests
./manage.sh test

# Help
./manage.sh help
```

---

## Summary

| Task | Command |
|------|---------|
| Start everything | `./manage.sh start-all` |
| Start UI only | `./manage.sh start-ui` |
| Start API only | `./manage.sh start-api` |
| Stop everything | `./manage.sh stop-all` |
| Check status | `./manage.sh status` |
| Run tests | `./manage.sh test` |
| View help | `./manage.sh help` |

---

## Support

For issues:
1. Check status: `./manage.sh status`
2. Review logs: `./manage.sh logs-ui`
3. See troubleshooting section above
4. Restart services: `./manage.sh stop-all && ./manage.sh start-all`

Enjoy learning Carnatic music! 🎵
