"""Test runner for the orchestrator agent.

Demonstrates the orchestrator agent routing queries to specialized sub-agents.
"""
import asyncio
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.plugins.logging_plugin import LoggingPlugin

from google.adk.runners import InMemoryRunner
from google.adk.apps import App
from google.genai import types

from carnatic_guru.orchestrator_agent.agent import root_agent as orchestrator_agent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_orchestrator():
    """Test the orchestrator agent with different types of queries."""
    
    logger.info("="*80)
    logger.info("CarnaticGuru Orchestrator Agent Test")
    logger.info("="*80)
    
    # Create app with orchestrator as root agent
    app = App(
        name="carnatic_guru",
        root_agent=orchestrator_agent,
        plugins=[LoggingPlugin()],
    )
    
    # Create in-memory runner for testing
    runner = InMemoryRunner(app=app)
    
    # Create session
    user_id = "test_user"
    session_id = "test_session"
    await runner.session_service.create_session(
        app_name=app.name,
        user_id=user_id,
        session_id=session_id,
        state={},
    )
    logger.info(f"✓ Session created: {session_id}\n")
    
    # Test queries that should route to different agents
    test_queries = [
        "Tell me about Sarali Varisai",
        "Generate swara patterns for Hamsadhwani raga",
        "What is Mayamalavagowla?",
    ]
    
    for idx, query in enumerate(test_queries, 1):
        logger.info(f"\n--- Query {idx}/{len(test_queries)} ---")
        logger.info(f"User: {query}\n")
        
        try:
            # Create message
            content = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )
            
            # Run through orchestrator and collect events
            events = []
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                events.append(event)
            
            # Display response from last agent event
            if events:
                for event in reversed(events):
                    if event.author != "user" and event.content and hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                logger.info(f"Agent: {part.text[:200]}...")
                                break
                        break
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("✓ Orchestrator agent test complete")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
