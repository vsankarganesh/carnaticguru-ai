"""CarnaticGuru Modern UI with Orchestrator Agent Integration.

Beautiful, responsive web interface for learning Carnatic music.

Features:
    - User selection (3 learners + Admin)
    - Persistent sessions per user
    - Integration with orchestrator agent
    - Real-time responses with streaming

Usage:
    python ui_app.py
    Visit: http://localhost:8002
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.adk.apps import App
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Import orchestrator agent as root
try:
    from carnatic_guru.orchestrator_agent.agent import root_agent as orchestrator_agent
except ModuleNotFoundError:
    import os
    import sys
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent_dir)
    from carnatic_guru.orchestrator_agent.agent import root_agent as orchestrator_agent

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & Constants
# ============================================================================

# Server configuration
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8002,
    "reload": False,
    "log_level": "info",
}

# Database configuration
DB_PATH = "carnatic_guru.db"

# ============================================================================
# Database Functions
# ============================================================================


def _get_users_from_db() -> Dict[str, Dict[str, str]]:
    """Load users from database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, avatar, color FROM users")
        rows = cursor.fetchall()
        conn.close()

        users = {}
        for row in rows:
            user_id, name, avatar, color = row
            users[user_id] = {
                "name": name,
                "avatar": avatar,
                "color": color,
            }
        return users
    except Exception as e:
        logger.error(f"Error loading users from database: {e}")
        # Return empty dict if database fails
        return {}


# Load users from database
USERS: Dict[str, Dict[str, str]] = _get_users_from_db()

# Fallback users if database is unavailable
FALLBACK_USERS = {
    "learner_1": {"name": "Arjun", "avatar": "👨‍🎓", "color": "#FF6B6B"},
    "learner_2": {"name": "Priya", "avatar": "👩‍🎓", "color": "#4ECDC4"},
    "learner_3": {"name": "Rohan", "avatar": "👨‍🎓", "color": "#45B7D1"},
    "admin": {"name": "Admin", "avatar": "👨‍💼", "color": "#95E1D3"},
}

# Use fallback if database load failed
if not USERS:
    logger.warning("Using fallback users (database unavailable)")
    USERS = FALLBACK_USERS

# Learning options - DEPRECATED (now handled by orchestrator)
LEARNING_OPTIONS: List[Dict[str, str]] = []

# ============================================================================
# Pydantic Models
# ============================================================================


class UserSelect(BaseModel):
    """User selection model."""
    user_id: str


class QueryRequest(BaseModel):
    """Query request model."""
    user_id: str
    query: str
    category: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model."""
    response: str
    user_name: str
    category: str
    timestamp: str


# ============================================================================
# Global State
# ============================================================================

# Service instances
session_service: Optional[DatabaseSessionService] = None
runner: Optional[Runner] = None
app_instance: Optional[App] = None

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="CarnaticGuru AI",
    description="Learn Carnatic Music with AI",
    version="1.0.0",
)


# ============================================================================
# Helper Functions
# ============================================================================


def _extract_user_name(user_id: str) -> str:
    """Extract user name from user ID."""
    if user_id not in USERS:
        raise ValueError(f"Invalid user ID: {user_id}")
    return USERS[user_id]["name"]


async def _extract_response_text(events: List) -> str:
    """Extract response text from events."""
    for event in reversed(events):
        if event.author != "user" and event.content:
            if hasattr(event.content, "parts") and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        return part.text
    return ""

# ============================================================================
# Service Initialization
# ============================================================================


async def init_services() -> None:
    """Initialize database, session service, and runner."""
    global session_service, runner, app_instance

    db_url = f"sqlite+aiosqlite:///{Path(DB_PATH).absolute()}"
    logger.info(f"Initializing with database: {db_url}")

    # Initialize session service
    session_service = DatabaseSessionService(db_url=db_url)



    # Create app with orchestrator as root agent
    app_instance = App(
        name="carnatic_guru",
        root_agent=orchestrator_agent,
        plugins=[LoggingPlugin()],
    )

    # Create runner with persistent sessions
    runner = Runner(
        app=app_instance,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )

    logger.info("✓ Services initialized successfully")

# ============================================================================
# API Endpoints - Users & Options
# ============================================================================


@app.get("/api/users")
async def get_users() -> Dict:
    """Get list of available users."""
    return {
        "users": [
            {
                "id": user_id,
                "name": profile["name"],
                "avatar": profile["avatar"],
                "color": profile["color"],
            }
            for user_id, profile in USERS.items()
        ]
    }


@app.get("/api/options")
async def get_learning_options() -> Dict:
    """Get available learning options."""
    return {"options": LEARNING_OPTIONS}

# ============================================================================
# API Endpoints - Query Processing
# ============================================================================


@app.post("/api/query")
async def run_query(request: QueryRequest) -> QueryResponse:
    """Process a query through the orchestrator agent."""
    # Validation
    if not runner or not session_service or not app_instance:
        raise HTTPException(status_code=503, detail="Services not initialized")

    if request.user_id not in USERS:
        raise HTTPException(status_code=400, detail="Invalid user")

    user_name = _extract_user_name(request.user_id)
    session_id = f"{request.user_id}_session"

    try:
        # Ensure session exists
        session = await session_service.get_session(
            app_name=app_instance.name,
            user_id=request.user_id,
            session_id=session_id,
        )

        if session is None:
            logger.info(f"Creating new session for {user_name}")
            session = await session_service.create_session(
                app_name=app_instance.name,
                user_id=request.user_id,
                session_id=session_id,
                state={"learning_history": []},
            )

        # Prepare query with context
        query_text = request.query
        if request.category:
            query_text = f"[{request.category}] {query_text}"

        # Create message
        content = types.Content(
            role="user",
            parts=[types.Part(text=query_text)]
        )

        logger.info(f"Processing query from {user_name}: {query_text[:100]}")

        # Collect events from runner
        events = []
        response_text = ""

        try:
            async for event in runner.run_async(
                user_id=request.user_id,
                session_id=session_id,
                new_message=content,
            ):
                events.append(event)
                # Extract response text from events as they arrive
                if event.author != "user" and event.content:
                    if hasattr(event.content, "parts") and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                response_text = part.text
        except Exception as e:
            logger.warning(f"Error during event streaming: {e}")
            if not response_text:
                response_text = "I encountered an issue processing your request. Please try again."

        # Fallback: extract from events if no response
        if not response_text and events:
            response_text = await _extract_response_text(events)

        logger.info(f"Response generated, events: {len(events)}")

        return QueryResponse(
            response=response_text or "Unable to generate response",
            user_name=user_name,
            category=request.category or "General",
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# API Endpoints - Session History
# ============================================================================


@app.get("/api/session/{user_id}")
async def get_session(user_id: str) -> Dict:
    """Get session history for a user."""
    if not session_service or not app_instance:
        raise HTTPException(status_code=503, detail="Services not initialized")

    if user_id not in USERS:
        raise HTTPException(status_code=400, detail="Invalid user")

    try:
        session_id = f"{user_id}_session"
        session = await session_service.get_session(
            app_name=app_instance.name,
            user_id=user_id,
            session_id=session_id,
        )

        events_data = []
        if session:
            for event in session.events:
                event_text = ""
                if event.content and hasattr(event.content, "parts") and event.content.parts:
                    if hasattr(event.content.parts[0], "text"):
                        event_text = event.content.parts[0].text

                events_data.append({
                    "author": event.author,
                    "text": event_text,
                })

        return {
            "session_id": session_id,
            "user_id": user_id,
            "num_events": len(events_data),
            "events": events_data,
        }

    except Exception as e:
        logger.error(f"Error retrieving session: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ============================================================================
# HTML UI Route
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    """Serve the main UI."""
    return get_ui_html()


def get_ui_html() -> str:
    """Generate the HTML UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CarnaticGuru AI - Learn Indian Classical Music</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            :root {
                --primary: #FF6B6B;
                --secondary: #4ECDC4;
                --accent: #45B7D1;
                --dark: #2C3E50;
                --light: #ECF0F1;
                --success: #2ECC71;
                --warning: #F39C12;
                --bg-primary: #1a1a1a;
                --bg-secondary: #2d2d2d;
                --text-primary: #e0e0e0;
                --text-secondary: #b0b0b0;
                --border-color: #3d3d3d;
            }
            
            :root.light-theme {
                --bg-primary: #ffffff;
                --bg-secondary: #f5f5f5;
                --text-primary: var(--dark);
                --text-secondary: #666;
                --border-color: #e0e0e0;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: var(--text-primary);
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            /* Header */
            header {
                background: var(--bg-primary);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
                border: 1px solid var(--border-color);
            }
            
            .logo {
                font-size: 28px;
                font-weight: bold;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .header-controls {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .user-selector {
                display: flex;
                gap: 10px;
                align-items: center;
                position: relative;
            }
            
            .user-dropdown {
                position: relative;
            }
            
            .dropdown-btn {
                padding: 10px 15px;
                border: 2px solid var(--border-color);
                border-radius: 25px;
                background: var(--bg-secondary);
                color: var(--text-primary);
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .dropdown-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                border-color: var(--primary);
            }
            
            .dropdown-menu {
                display: none;
                position: absolute;
                top: 100%;
                right: 0;
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 10px;
                margin-top: 8px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                min-width: 200px;
                z-index: 1000;
            }
            
            .dropdown-menu.active {
                display: block;
            }
            
            .dropdown-item {
                padding: 12px 20px;
                cursor: pointer;
                color: var(--text-primary);
                transition: all 0.2s ease;
                border-bottom: 1px solid var(--border-color);
                font-size: 14px;
            }
            
            .dropdown-item:last-child {
                border-bottom: none;
            }
            
            .dropdown-item:hover {
                background: var(--bg-primary);
                padding-left: 25px;
            }
            
            .dropdown-item.active {
                background: var(--primary);
                color: white;
            }
            
            .theme-toggle {
                padding: 10px 15px;
                border: 2px solid var(--border-color);
                border-radius: 25px;
                background: var(--bg-secondary);
                color: var(--text-primary);
                cursor: pointer;
                font-size: 16px;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .theme-toggle:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                border-color: var(--primary);
            }
            
            /* Main Content */
            .main-content {
                display: flex;
                flex-direction: column;
                gap: 20px;
                margin-bottom: 30px;
            }
            
            /* Sidebar - HIDDEN */
            .sidebar {
                display: none;
            }
            
            /* Chat Area - Full Width */
            .chat-area {
                background: var(--bg-primary);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                height: 600px;
                border: 1px solid var(--border-color);
                width: 100%;
            }
            
            .chat-header {
                padding-bottom: 15px;
                border-bottom: 2px solid var(--border-color);
                margin-bottom: 15px;
            }
            
            .chat-header h3 {
                color: var(--text-primary);
            }
            
            .messages {
                flex: 1;
                overflow-y: auto;
                margin-bottom: 15px;
                padding-right: 10px;
            }
            
            .message {
                margin-bottom: 15px;
                padding: 12px 15px;
                border-radius: 10px;
                word-wrap: break-word;
            }
            
            .message.user {
                background: linear-gradient(135deg, var(--primary), #FF8A8A);
                color: white;
                margin-left: 30px;
                text-align: right;
            }
            
            .message.assistant {
                background: var(--bg-secondary);
                color: var(--text-primary);
                margin-right: 30px;
                border-left: 4px solid var(--secondary);
            }
            
            .message-time {
                font-size: 12px;
                opacity: 0.7;
                margin-top: 5px;
            }
            
            .message.loading {
                background: var(--bg-secondary);
                color: var(--text-primary);
                text-align: center;
                font-style: italic;
            }
            
            /* Input Area */
            .input-area {
                display: flex;
                gap: 10px;
            }
            
            .query-input {
                flex: 1;
                padding: 12px 15px;
                border: 2px solid var(--border-color);
                border-radius: 25px;
                font-size: 14px;
                font-family: inherit;
                background: var(--bg-secondary);
                color: var(--text-primary);
                transition: border-color 0.3s ease;
            }
            
            .query-input::placeholder {
                color: var(--text-secondary);
            }
            
            .query-input:focus {
                outline: none;
                border-color: var(--primary);
            }
            
            .send-btn {
                padding: 12px 25px;
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .send-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(255, 107, 107, 0.4);
            }
            
            .send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }
            
            /* Sessions */
            .sessions-area {
                background: var(--bg-primary);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                border: 1px solid var(--border-color);
            }
            
            .sessions-area h3 {
                margin-bottom: 15px;
                color: var(--text-primary);
            }
            
            .session-item {
                padding: 12px;
                background: var(--bg-secondary);
                margin-bottom: 10px;
                border-radius: 8px;
                font-size: 13px;
                color: var(--text-secondary);
            }
            
            .session-item strong {
                color: var(--primary);
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                
                header {
                    flex-direction: column;
                    text-align: center;
                }
                
                .chat-area {
                    height: 400px;
                }
                
                .message {
                    margin-left: 10px !important;
                    margin-right: 10px !important;
                }
            }
            
            /* Loading Spinner */
            .spinner {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid rgba(0, 0, 0, 0.1);
                border-radius: 50%;
                border-top-color: var(--primary);
                animation: spin 0.8s linear infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            
            /* Scrollbar */
            .messages::-webkit-scrollbar {
                width: 8px;
            }
            
            .messages::-webkit-scrollbar-track {
                background: var(--bg-secondary);
                border-radius: 10px;
            }
            
            .messages::-webkit-scrollbar-thumb {
                background: var(--secondary);
                border-radius: 10px;
            }
            
            .messages::-webkit-scrollbar-thumb:hover {
                background: var(--primary);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo">🎵 CarnaticGuru AI</div>
                <div class="header-controls">
                    <div class="user-selector" id="userSelector">
                        <div class="user-dropdown">
                            <button class="dropdown-btn" id="userDropdownBtn">👤 Select User</button>
                            <div class="dropdown-menu" id="userDropdownMenu"></div>
                        </div>
                    </div>
                    <button class="theme-toggle" id="themeToggle">🌙</button>
                </div>
            </header>
            
            <div class="main-content">
                <div class="chat-area">
                    <div class="chat-header">
                        <h3 id="categoryTitle">🎵 CarnaticGuru AI Chat</h3>
                    </div>
                    <div class="messages" id="messagesContainer">
                        <div class="message assistant">
                            Welcome! 👋 Ask me anything about Carnatic music and I'll help you learn.
                        </div>
                    </div>
                    <div class="input-area">
                        <input 
                            type="text" 
                            class="query-input" 
                            id="queryInput" 
                            placeholder="Ask me anything about Carnatic music..."
                            disabled
                        >
                        <button class="send-btn" id="sendBtn" disabled>Send</button>
                    </div>
                </div>
            </div>
            
            <div class="sessions-area">
                <h3>📜 Session History</h3>
                <div id="sessionHistory">Select a user to view history</div>
            </div>
        </div>
        
        <script>
            let selectedUser = null;
            let selectedCategory = null;
            
            // ================================================================
            // Theme Management
            // ================================================================
            
            function initTheme() {
                const savedTheme = localStorage.getItem('theme') || 'dark';
                setTheme(savedTheme);
            }
            
            function setTheme(theme) {
                const root = document.documentElement;
                if (theme === 'light') {
                    root.classList.add('light-theme');
                    localStorage.setItem('theme', 'light');
                    document.getElementById('themeToggle').textContent = '☀️';
                } else {
                    root.classList.remove('light-theme');
                    localStorage.setItem('theme', 'dark');
                    document.getElementById('themeToggle').textContent = '🌙';
                }
            }
            
            function toggleTheme() {
                const root = document.documentElement;
                const isLight = root.classList.contains('light-theme');
                setTheme(isLight ? 'dark' : 'light');
            }
            
            // ================================================================
            // Initialization
            // ================================================================
            
            async function init() {
                initTheme();
                await loadUsers();
                setupEventListeners();
            }
            
            // ================================================================
            // User Management
            // ================================================================
            
            async function loadUsers() {
                try {
                    const res = await fetch('/api/users');
                    const data = await res.json();
                    
                    const dropdownMenu = document.getElementById('userDropdownMenu');
                    data.users.forEach(user => {
                        const item = document.createElement('div');
                        item.className = 'dropdown-item';
                        item.textContent = `${user.avatar} ${user.name}`;
                        item.onclick = () => selectUser(user.id, user.name, item);
                        dropdownMenu.appendChild(item);
                    });
                } catch (error) {
                    console.error('Error loading users:', error);
                }
            }
            
            function selectUser(userId, userName, itemElement) {
                selectedUser = userId;
                
                // Update dropdown button text
                document.getElementById('userDropdownBtn').textContent = `👤 ${userName}`;
                
                // Update active state
                document.querySelectorAll('.dropdown-item').forEach(item => {
                    item.classList.remove('active');
                });
                itemElement.classList.add('active');
                
                // Close dropdown
                document.getElementById('userDropdownMenu').classList.remove('active');
                
                // Enable input
                document.getElementById('queryInput').disabled = false;
                document.getElementById('sendBtn').disabled = false;
                
                // Load session history
                loadSessionHistory(userId);
            }
            
            function toggleUserDropdown() {
                const menu = document.getElementById('userDropdownMenu');
                menu.classList.toggle('active');
            }
            
            function closeUserDropdown() {
                document.getElementById('userDropdownMenu').classList.remove('active');
            }
            
            // ================================================================
            // Query Processing
            // ================================================================
            
            async function sendQuery() {
                const query = document.getElementById('queryInput').value.trim();
                
                if (!query) {
                    alert('Please enter a query!');
                    return;
                }
                
                if (!selectedUser) {
                    alert('Please select a user first!');
                    return;
                }
                
                await processQuery(query);
            }
            
            async function processQuery(query) {
                const messagesContainer = document.getElementById('messagesContainer');
                const queryInput = document.getElementById('queryInput');
                const sendBtn = document.getElementById('sendBtn');
                
                // Add user message
                const userMsg = document.createElement('div');
                userMsg.className = 'message user';
                userMsg.textContent = query;
                messagesContainer.appendChild(userMsg);
                
                // Clear input and disable controls
                queryInput.value = '';
                sendBtn.disabled = true;
                queryInput.disabled = true;
                
                // Add loading message
                const loadingMsg = document.createElement('div');
                loadingMsg.className = 'message loading';
                loadingMsg.innerHTML = '<span class="spinner"></span> Thinking...';
                messagesContainer.appendChild(loadingMsg);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                
                try {
                    const res = await fetch('/api/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: selectedUser,
                            query: query
                        })
                    });
                    
                    if (!res.ok) {
                        const error = await res.json();
                        throw new Error(error.detail || 'Query failed');
                    }
                    
                    const data = await res.json();
                    
                    // Remove loading message
                    loadingMsg.remove();
                    
                    // Add assistant response
                    const assistantMsg = document.createElement('div');
                    assistantMsg.className = 'message assistant';
                    assistantMsg.innerHTML = `${data.response}<div class="message-time">${new Date(data.timestamp).toLocaleTimeString()}</div>`;
                    messagesContainer.appendChild(assistantMsg);
                    
                    // Refresh session history
                    await loadSessionHistory(selectedUser);
                    
                } catch (error) {
                    loadingMsg.remove();
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'message assistant';
                    errorMsg.innerHTML = `❌ <strong>Error:</strong> ${error.message}`;
                    messagesContainer.appendChild(errorMsg);
                } finally {
                    sendBtn.disabled = false;
                    queryInput.disabled = false;
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    queryInput.focus();
                }
            }
            
            // ================================================================
            // Session History
            // ================================================================
            
            async function loadSessionHistory(userId) {
                try {
                    const res = await fetch(`/api/session/${userId}`);
                    const data = await res.json();
                    
                    const historyDiv = document.getElementById('sessionHistory');
                    if (data.num_events === 0) {
                        historyDiv.innerHTML = '📝 No history yet. Start learning!';
                    } else {
                        let html = `<strong>${data.num_events} events in session:</strong><br>`;
                        data.events.slice(-5).forEach((event) => {
                            const preview = event.text.substring(0, 60) + (event.text.length > 60 ? '...' : '');
                            html += `<div class="session-item"><strong>${event.author}:</strong> ${preview}</div>`;
                        });
                        historyDiv.innerHTML = html;
                    }
                } catch (error) {
                    console.error('Error loading history:', error);
                }
            }
            
            // ================================================================
            // Event Listeners
            // ================================================================
            
            function setupEventListeners() {
                document.getElementById('sendBtn').onclick = sendQuery;
                
                document.getElementById('queryInput').onkeypress = (e) => {
                    if (e.key === 'Enter') {
                        sendQuery();
                    }
                };
                
                document.getElementById('themeToggle').onclick = toggleTheme;
                
                document.getElementById('userDropdownBtn').onclick = toggleUserDropdown;
                
                // Close dropdown when clicking outside
                document.onclick = (e) => {
                    const dropdown = document.getElementById('userDropdownMenu');
                    const btn = document.getElementById('userDropdownBtn');
                    if (e.target !== btn && !btn.contains(e.target) && !dropdown.contains(e.target)) {
                        closeUserDropdown();
                    }
                };
            }
            
            // ================================================================
            // Start Application
            // ================================================================
            
            init();
        </script>
    </body>
    </html>
    """

# ============================================================================
# Startup & Shutdown
# ============================================================================


@app.on_event("startup")
async def startup() -> None:
    """Initialize services on startup."""
    logger.info("\n" + "=" * 80)
    logger.info("🎵 CarnaticGuru UI Starting")
    logger.info("=" * 80)
    await init_services()
    logger.info("=" * 80)
    logger.info("✓ UI Server Ready!")
    logger.info(f"📍 Visit: http://localhost:{SERVER_CONFIG['port']}")
    logger.info("=" * 80 + "\n")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
        log_level=SERVER_CONFIG["log_level"],
    )
