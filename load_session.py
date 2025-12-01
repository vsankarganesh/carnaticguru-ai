"""Load and continue a persisted session from SQLite database.

This script demonstrates how to:
1. Load a previously persisted session from carnatic_guru.db
2. View the conversation history
3. Continue the conversation with new queries
"""
import asyncio
import logging
from pathlib import Path

from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
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


async def main():
    """Load persisted session and continue conversation."""
    
    logger.info("="*80)
    logger.info("CarnaticGuru Session Loader - Continuing Persisted Conversation")
    logger.info("="*80)
    
    db_path = "carnatic_guru.db"
    db_url = f"sqlite+aiosqlite:///{Path(db_path).absolute()}"
    
    # Verify database exists
    if not Path(db_path).exists():
        logger.error(f"Database not found: {db_path}")
        logger.info("Please run runner_persistent.py first to create a session.")
        return
    
    logger.info(f"\nDatabase found: {db_path}")
    logger.info(f"Database size: {Path(db_path).stat().st_size / 1024:.2f} KB")
    
    # Initialize session service
    session_service = DatabaseSessionService(db_url=db_url)
    
    # Create the root agent with sub-agents
    root_agent = lesson_agent
    root_agent.sub_agents = [pattern_agent, raga_agent]
    
    # Create app
    app = App(
        name="carnatic_guru",
        root_agent=root_agent,
    )
    
    # Create runner
    runner = Runner(
        app=app,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    
    user_id = "persistent_user"
    session_id = "persistent_session_1"
    
    # Load the existing session
    logger.info(f"\nLoading session: {session_id}")
    session = await session_service.get_session(
        app_name=app.name,
        user_id=user_id,
        session_id=session_id,
    )
    
    if not session:
        logger.error(f"Session not found: {session_id}")
        return
    
    # Display conversation history
    logger.info(f"\n--- Conversation History ({len(session.events)} events) ---\n")
    for idx, event in enumerate(session.events, 1):
        if event.author == "user" and event.content and event.content.parts:
            text = event.content.parts[0].text if event.content.parts[0].text else "(empty)"
            logger.info(f"{idx}. User: {text[:80]}")
        elif event.author != "user" and event.content and event.content.parts:
            text = event.content.parts[0].text if event.content.parts[0].text else "(empty)"
            logger.info(f"{idx}. {event.author}: {text[:80]}...")
    
    # Continue with a new query
    logger.info(f"\n--- Continuing Conversation ---\n")
    new_query = "Thank you! Can you give me a Janta Varisai exercise example?"
    logger.info(f"New query: {new_query}")
    
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=new_query)]
    )
    
    logger.info("\nAgent responses:")
    events = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=new_message,
    ):
        events.append(event)
        if event.author != "user" and event.content and event.content.parts:
            if event.content.parts[0].text:
                text = event.content.parts[0].text[:120]
                logger.info(f"  → {event.author}: {text}...")
    
    logger.info(f"\n✓ Received {len(events)} new events")
    
    # Display updated session statistics
    logger.info(f"\n--- Updated Session Info ---")
    updated_session = await session_service.get_session(
        app_name=app.name,
        user_id=user_id,
        session_id=session_id,
    )
    if updated_session:
        logger.info(f"  - Total events now: {len(updated_session.events)}")
        logger.info(f"  - Session state: {updated_session.state}")
    
    logger.info("\n" + "="*80)
    logger.info("✓ Session continuation completed!")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
