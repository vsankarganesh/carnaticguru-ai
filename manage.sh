#!/bin/bash
# CarnaticGuru AI - Application Launcher & Manager
# Provides easy commands to start, stop, and manage all services

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        echo "Please run: python3 -m venv .venv"
        exit 1
    fi
}

activate_venv() {
    check_venv
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
}

# ============================================================================
# Start Functions
# ============================================================================

start_ui() {
    print_header "🎵 Starting CarnaticGuru UI (Port 8002)"
    
    activate_venv
    
    # Kill any existing process on port 8002
    if lsof -i :8002 > /dev/null 2>&1; then
        print_warning "Port 8002 is in use, attempting to free it..."
        lsof -ti:8002 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    print_info "Starting FastAPI server..."
    cd "$PROJECT_DIR"
    python ui_app.py &
    UI_PID=$!
    sleep 3
    
    if lsof -i :8002 > /dev/null 2>&1; then
        print_success "UI Server started (PID: $UI_PID)"
        print_info "URL: http://localhost:8002"
    else
        print_error "Failed to start UI server"
        exit 1
    fi
}

start_orchestrator_cli() {
    print_header "🎼 Starting Orchestrator CLI (Interactive)"
    
    activate_venv
    
    print_info "Starting interactive orchestrator..."
    cd "$PROJECT_DIR"
    python orchestrator_persistent.py
}

start_web_api() {
    print_header "🌐 Starting Web API (Port 8001)"
    
    activate_venv
    
    # Kill any existing process on port 8001
    if lsof -i :8001 > /dev/null 2>&1; then
        print_warning "Port 8001 is in use, attempting to free it..."
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    print_info "Starting web API server..."
    cd "$PROJECT_DIR"
    python web_app.py &
    WEB_PID=$!
    sleep 3
    
    if lsof -i :8001 > /dev/null 2>&1; then
        print_success "Web API started (PID: $WEB_PID)"
        print_info "URL: http://localhost:8001"
    else
        print_error "Failed to start Web API"
        exit 1
    fi
}

start_persistent_cli() {
    print_header "📚 Starting Persistent CLI Runner"
    
    activate_venv
    
    print_info "Starting persistent CLI runner..."
    cd "$PROJECT_DIR"
    python runner_persistent.py
}

start_all() {
    print_header "🚀 Starting All Services"
    
    activate_venv
    
    # Kill any existing processes - be very aggressive
    print_info "Cleaning up any existing processes..."
    pkill -9 -f "python ui_app.py" 2>/dev/null || true
    pkill -9 -f "python web_app.py" 2>/dev/null || true
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Start UI
    print_info "Starting UI server..."
    cd "$PROJECT_DIR"
    python ui_app.py > /tmp/ui.log 2>&1 &
    UI_PID=$!
    sleep 3
    
    if lsof -i :8002 > /dev/null 2>&1; then
        print_success "UI Server started (PID: $UI_PID)"
        print_info "  URL: http://localhost:8002"
    else
        print_error "Failed to start UI server"
        exit 1
    fi
    
    # Start Web API
    print_info "Starting Web API server..."
    python web_app.py > /tmp/web_api.log 2>&1 &
    WEB_PID=$!
    sleep 3
    
    if lsof -i :8001 > /dev/null 2>&1; then
        print_success "Web API started (PID: $WEB_PID)"
        print_info "  URL: http://localhost:8001"
    else
        print_error "Failed to start Web API"
    fi
    
    print_header "✅ All Services Started"
    echo ""
    echo "Services running:"
    echo "  🎵 UI Dashboard:  http://localhost:8002"
    echo "  🌐 Web API:       http://localhost:8001"
    echo ""
    echo "To stop services, run: ./manage.sh stop-all"
    echo ""
}

# ============================================================================
# Stop Functions
# ============================================================================

restart_all() {
    print_header "🔄 Restarting All Services"
    
    # Stop all services
    print_info "Stopping all services..."
    pkill -f "python ui_app.py" 2>/dev/null || true
    pkill -f "python web_app.py" 2>/dev/null || true
    pkill -f "python orchestrator_persistent.py" 2>/dev/null || true
    pkill -f "python runner_persistent.py" 2>/dev/null || true
    
    # Clear any lingering processes on ports
    print_info "Clearing ports 8001 and 8002..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Verify ports are free
    if lsof -i :8001 > /dev/null 2>&1 || lsof -i :8002 > /dev/null 2>&1; then
        print_warning "Some ports still in use, waiting..."
        sleep 2
    fi
    
    print_info "All services stopped, waiting before restart..."
    sleep 1
    
    # Start all services
    activate_venv
    
    print_info "Starting UI server..."
    cd "$PROJECT_DIR"
    python ui_app.py > /tmp/ui.log 2>&1 &
    UI_PID=$!
    sleep 3
    
    if lsof -i :8002 > /dev/null 2>&1; then
        print_success "UI Server started (PID: $UI_PID)"
        print_info "  URL: http://localhost:8002"
    else
        print_error "Failed to start UI server"
        exit 1
    fi
    
    # Start Web API
    print_info "Starting Web API server..."
    python web_app.py > /tmp/web_api.log 2>&1 &
    WEB_PID=$!
    sleep 3
    
    if lsof -i :8001 > /dev/null 2>&1; then
        print_success "Web API started (PID: $WEB_PID)"
        print_info "  URL: http://localhost:8001"
    else
        print_warning "Failed to start Web API (non-fatal)"
    fi
    
    print_header "✅ All Services Restarted"
    echo ""
    echo "Services running:"
    echo "  🎵 UI Dashboard:  http://localhost:8002"
    echo "  🌐 Web API:       http://localhost:8001"
    echo ""
    echo "💡 Tip: Clear browser cache if you still see old content"
    echo "   Mac: Cmd+Shift+R (Chrome/Edge), Cmd+Shift+Delete (Firefox)"
    echo ""
}

# ============================================================================
# Stop Functions
# ============================================================================

stop_ui() {
    print_header "🎵 Stopping UI Server"
    
    if lsof -i :8002 > /dev/null 2>&1; then
        print_info "Killing process on port 8002..."
        lsof -ti:8002 | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "UI Server stopped"
    else
        print_warning "No process found on port 8002"
    fi
}

stop_web_api() {
    print_header "🌐 Stopping Web API"
    
    if lsof -i :8001 > /dev/null 2>&1; then
        print_info "Killing process on port 8001..."
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "Web API stopped"
    else
        print_warning "No process found on port 8001"
    fi
}

stop_all() {
    print_header "🛑 Stopping All Services"
    
    print_info "Stopping UI server..."
    pkill -f "python ui_app.py" 2>/dev/null || true
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    
    print_info "Stopping Web API..."
    pkill -f "python web_app.py" 2>/dev/null || true
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    
    print_info "Stopping other Python processes..."
    pkill -f "python orchestrator_persistent.py" 2>/dev/null || true
    pkill -f "python runner_persistent.py" 2>/dev/null || true
    
    sleep 2
    
    # Verify services stopped
    if ! lsof -i :8002 > /dev/null 2>&1 && ! lsof -i :8001 > /dev/null 2>&1; then
        print_success "All services stopped"
    else
        print_warning "Ports still in use, forcing cleanup..."
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        lsof -ti:8002 | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "All services stopped (forced)"
    fi
}

# ============================================================================
# Status Functions
# ============================================================================

status() {
    print_header "📊 Service Status"
    
    echo ""
    
    if lsof -i :8002 > /dev/null 2>&1; then
        print_success "UI Server (port 8002) is RUNNING"
        echo "  → http://localhost:8002"
    else
        print_error "UI Server (port 8002) is STOPPED"
    fi
    
    if lsof -i :8001 > /dev/null 2>&1; then
        print_success "Web API (port 8001) is RUNNING"
        echo "  → http://localhost:8001"
    else
        print_error "Web API (port 8001) is STOPPED"
    fi
    
    echo ""
    echo "Python processes:"
    ps aux | grep -E "python.*app\.py" | grep -v grep || print_warning "No app processes running"
    
    echo ""
}

# ============================================================================
# Test Functions
# ============================================================================

test_ui() {
    print_header "🧪 Testing UI Integration"
    
    activate_venv
    
    if ! lsof -i :8002 > /dev/null 2>&1; then
        print_error "UI Server is not running"
        print_info "Start it with: ./manage.sh start-ui"
        exit 1
    fi
    
    print_info "Testing orchestrator integration..."
    cd "$PROJECT_DIR"
    python test_orchestrator_ui.py
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    cat << 'EOF'

🎵 CarnaticGuru AI - Application Manager

USAGE: ./manage.sh <command>

COMMANDS:
  
  START SERVICES:
    start-ui              Start UI server (port 8002)
    start-api             Start Web API (port 8001)
    start-cli             Start Orchestrator CLI (interactive)
    start-persistent      Start Persistent CLI runner
    start-all             Start all services (UI + API)
  
  STOP SERVICES:
    stop-ui               Stop UI server
    stop-api              Stop Web API
    stop-all              Stop all services
  
  RESTART SERVICES:
    restart-all           Stop all services and start them again
  
  STATUS & MANAGEMENT:
    status                Show status of all services
    logs-ui               Show UI server logs
    logs-api              Show Web API logs
    test                  Run integration tests
  
  UTILITY:
    help                  Show this help message

QUICK START:

  1. Start all services:
     ./manage.sh start-all

  2. Open in browser:
     http://localhost:8002

  3. Stop when done:
     ./manage.sh stop-all

EXAMPLES:

  # Start UI only
  ./manage.sh start-ui

  # Check status
  ./manage.sh status

  # Restart all services
  ./manage.sh restart-all

  # Stop all
  ./manage.sh stop-all

  # Run tests
  ./manage.sh test

TROUBLESHOOTING:

  If you still see the application after stopping:
    1. Clear your browser cache (Cmd+Shift+R on Mac)
    2. Open DevTools → Application → Clear All → Refresh
    3. Try restart-all command

EOF
}

# ============================================================================
# Logs Functions
# ============================================================================

logs_ui() {
    print_header "📋 UI Server Logs"
    tail -f /tmp/ui.log 2>/dev/null || print_error "No UI logs found"
}

logs_api() {
    print_header "📋 Web API Logs"
    tail -f /tmp/web_api.log 2>/dev/null || print_error "No Web API logs found"
}

# ============================================================================
# Main
# ============================================================================

COMMAND="${1:-help}"

case "$COMMAND" in
    start-ui)
        start_ui
        ;;
    start-api)
        start_web_api
        ;;
    start-cli)
        start_orchestrator_cli
        ;;
    start-persistent)
        start_persistent_cli
        ;;
    start-all)
        start_all
        ;;
    stop-ui)
        stop_ui
        ;;
    stop-api)
        stop_web_api
        ;;
    stop-all)
        stop_all
        ;;
    restart-all)
        restart_all
        ;;
    status)
        status
        ;;
    logs-ui)
        logs_ui
        ;;
    logs-api)
        logs_api
        ;;
    test)
        test_ui
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
