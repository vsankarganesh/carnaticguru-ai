"""CarnaticGuru Web Application with Persistent Sessions.

FastAPI web interface with persistent SQLite-backed sessions and multi-agent support.

Usage:
  python web_app.py

Then visit: http://localhost:8000 in your browser
Or use curl: curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "Explain swarams", "session_id": "test_session"}'
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

# Import the orchestrator agent
from carnatic_guru.orchestrator_agent.agent import orchestrator_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for API
# ============================================================================

class QueryRequest(BaseModel):
    """Request to run a query against the agents."""
    query: str
    session_id: str = "web_session_1"
    user_id: str = "web_user"


class SessionInfo(BaseModel):
    """Information about a session."""
    session_id: str
    user_id: str
    app_name: str
    created_at: Optional[str] = None
    event_count: int = 0


class QueryResponse(BaseModel):
    """Response from agent query."""
    query: str
    response: str
    agent_name: str
    session_id: str
    event_count: int
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    db_path: str
    agents: list
    timestamp: str


# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="CarnaticGuru AI",
    description="Learn Carnatic music with AI-powered lessons, patterns, and raga information.",
    version="1.0.0"
)

# Global state
db_url: Optional[str] = None
session_service: Optional[DatabaseSessionService] = None
runner: Optional[Runner] = None
adk_app: Optional[App] = None


# ============================================================================
# Initialization
# ============================================================================

async def init_services(db_path: str = "carnatic_guru.db"):
    """Initialize database, session service, runner, and app."""
    global db_url, session_service, runner, adk_app
    
    # Setup database
    db_url = f"sqlite+aiosqlite:///{Path(db_path).absolute()}"
    logger.info(f"Initializing with database: {db_url}")
    
    # Create session service
    session_service = DatabaseSessionService(db_url=db_url)
    
    # Create root agent
    root_agent = orchestrator_agent
    
    # Create app - using app_name that matches the runner's expectation
    adk_app = App(
        name="agents",  # Use the inferred app name from agent directory
        root_agent=root_agent,
    )
    
    # Create runner with persistent sessions
    runner = Runner(
        app=adk_app,
        session_service=session_service,
    )
    
    logger.info(f"✓ Database initialized: {db_path}")
    logger.info(f"✓ Root agent: {root_agent.name}")
    logger.info(f"✓ App name: {adk_app.name}")
    logger.info(f"✓ Runner ready with persistent sessions")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not runner or not adk_app:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    return HealthResponse(
        status="healthy",
        db_path=db_url or "unknown",
        agents=[
            orchestrator_agent.name,
        ],
        timestamp=datetime.now().isoformat(),
    )


@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """Run a query against the CarnaticGuru agents with persistent sessions."""
    if not runner or not session_service or not adk_app:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        # Ensure session exists
        session = await session_service.get_session(
            app_name=adk_app.name,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        
        if session is None:
            logger.info(f"Creating new session: {request.session_id}")
            session = await session_service.create_session(
                app_name=adk_app.name,
                user_id=request.user_id,
                session_id=request.session_id,
                state={},
            )
            logger.info(f"✓ Session created: {session.id}")
        else:
            logger.info(f"✓ Using existing session: {request.session_id}")
        
        # Run query
        content = types.Content(
            role="user",
            parts=[types.Part(text=request.query)]
        )
        
        logger.info(f"Processing query from {request.user_id} (session: {request.session_id})")
        logger.info(f"Query: {request.query}")
        
        # Collect all events from the generator
        events = []
        async def collect_events():
            async for event in runner.run_async(
                user_id=request.user_id,
                session_id=request.session_id,
                new_message=content,
            ):
                events.append(event)
        
        # Run with timeout
        await asyncio.wait_for(
            collect_events(),
            timeout=30.0
        )
        
        # Extract response from the last event
        response_text = ""
        agent_name = "unknown"
        
        if events:
            last_event = events[-1]
            if hasattr(last_event, 'output') and last_event.output:
                if hasattr(last_event.output, 'parts'):
                    for part in last_event.output.parts:
                        if hasattr(part, 'text'):
                            response_text = part.text
                            break
            
            # Try to determine which agent responded from agent name in event
            if hasattr(last_event, 'agent_name'):
                agent_name = last_event.agent_name

        
        # Get updated session info
        session = await session_service.get_session(
            app_name=adk_app.name,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        
        event_count = len(session.events) if hasattr(session, 'events') else 0
        
        logger.info(f"✓ Response from {agent_name}")
        logger.info(f"  Events in session: {event_count}")
        
        return QueryResponse(
            query=request.query,
            response=response_text,
            agent_name=agent_name,
            session_id=request.session_id,
            event_count=event_count,
            timestamp=datetime.now().isoformat(),
        )
    
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Query timeout (30 seconds)")
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/session/{session_id}")
async def get_session_info(session_id: str, user_id: str = "web_user"):
    """Get information about a session including event history."""
    if not session_service or not adk_app:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        session = await session_service.get_session(
            app_name=adk_app.name,
            user_id=user_id,
            session_id=session_id,
        )
        
        events = []
        if hasattr(session, 'events'):
            for event in session.events:
                if hasattr(event, 'to_dict'):
                    events.append(event.to_dict())
                else:
                    events.append(str(event))
        
        return JSONResponse({
            "session_id": session_id,
            "user_id": user_id,
            "app_name": adk_app.name,
            "event_count": len(events),
            "events": events,
        })
    except Exception as e:
        logger.error(f"Error retrieving session: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("\n" + "="*80)
    logger.info("CarnaticGuru Web Server Starting")
    logger.info("="*80)
    await init_services("carnatic_guru.db")
    logger.info("="*80)
    logger.info("Server ready! Available endpoints:")
    logger.info("  GET  /health               - Health check")
    logger.info("  POST /query                - Run a query")
    logger.info("  GET  /session/{session_id} - Get session history")
    logger.info("="*80)
    logger.info("Example requests:")
    logger.info('  curl http://localhost:8000/health')
    logger.info('  curl -X POST http://localhost:8000/query \\')
    logger.info('    -H "Content-Type: application/json" \\')
    logger.info('    -d \'{"query": "Explain swarams", "session_id": "test_1"}\'')
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
    )
