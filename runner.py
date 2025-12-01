"""CarnaticGuru multi-agent runner.

Runs lesson_agent, pattern_agent, and raga_agent together using ADK's App and InMemoryRunner.
"""
import asyncio
import logging

from google.adk.runners import InMemoryRunner
from google.adk.apps import App
from google import genai

# Import the three agents
from carnatic_guru.lesson_agent.agent import lesson_agent
from carnatic_guru.pattern_agent.agent import pattern_agent
from carnatic_guru.raga_agent.agent import raga_agent
from carnatic_guru.orchestrator_agent.agent import OrchestratorAgent 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run all three agents with a multi-agent app."""
    
    # Create the root agent (LessonAgent) with sub-agents
    root_agent = OrchestratorAgent
    #root_agent.sub_agents = [pattern_agent, raga_agent]
    
    # Create app with the root agent
    app = App(
        name="carnatic_guru",
        root_agent=root_agent,
    )
    
    # Create runner with in-memory services
    runner = InMemoryRunner(app=app)
    
    # Test queries for each agent
    user_id = "test_user"
    session_id = "test_session"
    queries = [
        "Tell me about Sarali Varisai",
        "Generate 3 patterns for Hamsadhwani raga",
        "What is the Kalyani raga? Give me the arohana and famous compositions.",
    ]
    
    for idx, query in enumerate(queries, 1):
        logger.info(f"\n=== Test {idx}: {query} ===")
        try:
            events = await runner.run_debug(
                query,
                user_id=user_id,
                session_id=session_id,
                quiet=False,
                verbose=False,
            )
            logger.info(f"✓ Test {idx} passed: {len(events)} events returned")
        except Exception as e:
            logger.error(f"✗ Test {idx} failed: {e}", exc_info=True)
        print("\n" + "="*80)
    
    logger.info("\n✓ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
