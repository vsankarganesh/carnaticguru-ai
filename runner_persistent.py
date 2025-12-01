"""CarnaticGuru persistent runner with SQLite database.

Uses google.adk.sessions.DatabaseSessionService to persist conversation sessions
across invocations. Stores sessions in carnatic_guru.db.
"""
import asyncio
import logging
import os
from pathlib import Path

from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google import genai
from google.genai import types

# Import the three agents
from carnatic_guru.lesson_agent.agent import lesson_agent
from carnatic_guru.pattern_agent.agent import pattern_agent
from carnatic_guru.raga_agent.agent import raga_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PersistentRunner:
    """Runner with persistent SQLite session storage."""
    
    def __init__(self, db_path: str = "carnatic_guru.db"):
        """Initialize persistent runner with SQLite database.
        
        Args:
            db_path: Path to SQLite database file (default: carnatic_guru.db)
        """
        self.db_path = db_path
        self.db_url = f"sqlite+aiosqlite:///{os.path.abspath(db_path)}"
        logger.info(f"Initializing DatabaseSessionService with: {self.db_url}")
        
        # Create DatabaseSessionService with async SQLite
        self.session_service = DatabaseSessionService(db_url=self.db_url)
        
        # Create the root agent with sub-agents
        self.root_agent = lesson_agent
        self.root_agent.sub_agents = [pattern_agent, raga_agent]
        
        # Create app
        self.app = App(
            name="carnatic_guru",
            root_agent=self.root_agent,
        )
        
        # Create runner with persistent session service
        self.runner = Runner(
            app=self.app,
            session_service=self.session_service,
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
        )
    
    async def run_query(self, query: str, user_id: str, session_id: str) -> None:
        """Run a single query and persist to database.
        
        Args:
            query: User query to send to agent
            user_id: User identifier for session management
            session_id: Session identifier for conversation persistence
        """
        logger.info(f"Running query: {query}")
        try:
            # Create or get session
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
            if not session:
                logger.info(f"Creating new session: {session_id}")
                session = await self.session_service.create_session(
                    app_name=self.app.name,
                    user_id=user_id,
                    session_id=session_id,
                    state={},
                )
            
            # Create Content object from query string
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )
            
            events = []
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
            ):
                events.append(event)
                if event.author != "user" and event.content:
                    parts = event.content.parts if event.content.parts else []
                    if parts and parts[0].text:
                        text = parts[0].text[:120]
                        logger.info(f"  → {event.author}: {text}...")
            
            logger.info(f"✓ Query completed with {len(events)} events")
        except Exception as e:
            logger.error(f"Error running query: {e}", exc_info=True)
    
    async def get_session_history(self, user_id: str, session_id: str) -> dict:
        """Retrieve session history from persistent storage.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session data with all events and state
        """
        try:
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
            if session:
                logger.info(f"Session found: {len(session.events)} events, state: {session.state}")
                return {
                    "id": session.id,
                    "user_id": session.user_id,
                    "num_events": len(session.events),
                    "state": session.state,
                }
            else:
                logger.warning(f"Session not found: {session_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving session: {e}", exc_info=True)
            return None


async def demo_persistent_sessions():
    """Demonstrate persistent session storage across multiple invocations."""
    
    logger.info("="*80)
    logger.info("CarnaticGuru Persistent Runner Demo")
    logger.info("="*80)
    
    # Initialize persistent runner
    runner = PersistentRunner(db_path="carnatic_guru.db")
    
    user_id = "persistent_user"
    session_id = "persistent_session_1"
    
    # Demo: Multiple queries in same session (should persist)
    queries = [
        "Tell me about Sarali Varisai",
        "What is Mayamalavagowla raga?",
        "Generate patterns for Hamsadhwani",
    ]
    
    logger.info("\n--- Phase 1: Running queries (persisting to database) ---\n")
    for idx, query in enumerate(queries, 1):
        logger.info(f"\nQuery {idx}/{len(queries)}")
        await runner.run_query(query, user_id, session_id)
        print("\n" + "="*80)
    
    # Demo: Retrieve session history from persistent storage
    logger.info("\n--- Phase 2: Retrieving session history from database ---\n")
    session_info = await runner.get_session_history(user_id, session_id)
    if session_info:
        logger.info(f"✓ Session persisted in database:")
        logger.info(f"  - Session ID: {session_info['id']}")
        logger.info(f"  - User ID: {session_info['user_id']}")
        logger.info(f"  - Total events: {session_info['num_events']}")
        logger.info(f"  - Session state: {session_info['state']}")
    
    # Demo: Verify database file was created
    logger.info("\n--- Phase 3: Verifying database file ---\n")
    db_file = Path(runner.db_path)
    if db_file.exists():
        size_kb = db_file.stat().st_size / 1024
        logger.info(f"✓ Database file created: {runner.db_path} ({size_kb:.2f} KB)")
    else:
        logger.warning(f"Database file not found: {runner.db_path}")
    
    logger.info("\n" + "="*80)
    logger.info("✓ Demo completed successfully!")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(demo_persistent_sessions())
