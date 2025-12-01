"""Persistent orchestrator runner with SQLite session storage.

This runner wraps the OrchestratorAgent with DatabaseSessionService to persist
all conversations across invocations. All agents (lesson, pattern, raga) maintain
context through the shared session.

Usage:
  python orchestrator_persistent.py
  
Sessions are stored in: carnatic_guru.db
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.sessions import DatabaseSessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai import types

# Import orchestrator agent
from carnatic_guru.orchestrator_agent.agent import root_agent as orchestrator_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PersistentOrchestratorRunner:
    """Orchestrator runner with persistent session storage."""
    
    def __init__(self, db_path: str = "carnatic_guru.db"):
        """Initialize persistent orchestrator runner.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_url = f"sqlite+aiosqlite:///{Path(db_path).absolute()}"
        
        # Create DatabaseSessionService with async SQLite
        self.session_service = DatabaseSessionService(db_url=self.db_url)
        
        # Create app with orchestrator as root agent
        self.app = App(
            name="carnatic_guru",
            root_agent=orchestrator_agent,
        )
        
        # Create runner with persistent session service
        self.runner = Runner(
            app=self.app,
            session_service=self.session_service,
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
        )
        
        logger.info(f"✓ Initialized with database: {db_path}")
        logger.info(f"✓ App: {self.app.name}")
        logger.info(f"✓ Root Agent: {orchestrator_agent.name}")
    
    async def run_query(self, query: str, user_id: str, session_id: str) -> str:
        """Run a query and persist to database.
        
        Args:
            query: User query
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Agent response text
        """
        try:
            # Ensure session exists
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
            
            if session is None:
                logger.info(f"Creating new session: {session_id}")
                session = await self.session_service.create_session(
                    app_name=self.app.name,
                    user_id=user_id,
                    session_id=session_id,
                    state={},
                )
            
            # Create message
            content = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )
            
            logger.info(f"Query: {query}")
            
            # Collect events from runner
            events = []
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                events.append(event)
            
            # Extract response
            response_text = ""
            if events:
                for event in reversed(events):
                    if event.author != "user" and event.content and hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                response_text = part.text
                                break
                        if response_text:
                            break
            
            logger.info(f"Events saved: {len(events)}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return f"Error: {str(e)}"
    
    async def get_session_history(self, user_id: str, session_id: str) -> dict:
        """Get full session history from persistent storage.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session data with events and metadata
        """
        try:
            session = await self.session_service.get_session(
                app_name=self.app.name,
                user_id=user_id,
                session_id=session_id,
            )
            
            if session:
                events_data = []
                for event in session.events:
                    event_text = ""
                    if event.content and hasattr(event.content, 'parts') and event.content.parts:
                        if hasattr(event.content.parts[0], 'text'):
                            event_text = event.content.parts[0].text[:100]
                    
                    events_data.append({
                        "author": event.author,
                        "type": event.type if hasattr(event, 'type') else "unknown",
                        "text": event_text,
                    })
                
                return {
                    "session_id": session.id,
                    "user_id": session.user_id,
                    "app_name": session.app_name,
                    "num_events": len(session.events),
                    "events": events_data
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            return None
    
    async def interactive_session(self, user_id: str = "persistent_user"):
        """Run an interactive session with persistence.
        
        Args:
            user_id: User identifier for session
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info("\n" + "="*80)
        logger.info("CarnaticGuru Persistent Orchestrator - Interactive Mode")
        logger.info("="*80)
        logger.info(f"Session: {session_id}")
        logger.info(f"User: {user_id}")
        logger.info(f"Database: {self.db_path}")
        logger.info("Type 'exit' to quit, 'history' to see session history")
        logger.info("="*80 + "\n")
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() == "exit":
                    logger.info("Goodbye!")
                    break
                
                if query.lower() == "history":
                    history = await self.get_session_history(user_id, session_id)
                    if history:
                        logger.info(f"\nSession History ({history['num_events']} events):")
                        for i, event in enumerate(history.get('events', []), 1):
                            author = event.get('author', 'unknown')
                            text = event.get('text', '')[:80]
                            logger.info(f"  {i}. {author}: {text}")
                        logger.info()
                    else:
                        logger.info("No history available")
                    continue
                
                if not query:
                    continue
                
                response = await self.run_query(query, user_id, session_id)
                print(f"\nAgent: {response}\n")
                
            except EOFError:
                logger.info("Session ended")
                break
            except KeyboardInterrupt:
                logger.info("\nSession interrupted")
                break
            except Exception as e:
                logger.error(f"Error: {e}")


async def main():
    """Main entry point."""
    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "history":
        # Show history for a specific session
        user_id = sys.argv[2] if len(sys.argv) > 2 else "persistent_user"
        session_id = sys.argv[3] if len(sys.argv) > 3 else "session_default"
        
        runner = PersistentOrchestratorRunner()
        history = await runner.get_session_history(user_id, session_id)
        
        if history:
            logger.info(f"\nSession: {history['session_id']}")
            logger.info(f"User: {history['user_id']}")
            logger.info(f"Total Events: {history['num_events']}\n")
            
            for i, event in enumerate(history['events'], 1):
                logger.info(f"{i}. [{event['author']}]: {event['text']}")
        else:
            logger.info(f"Session not found: {session_id}")
        
        return
    
    # Run interactive session
    runner = PersistentOrchestratorRunner()
    await runner.interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
