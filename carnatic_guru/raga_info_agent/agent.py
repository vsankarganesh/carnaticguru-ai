import sys
import os
from pathlib import Path

# Add parent directory to path BEFORE any imports of carnatic_guru
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import carnatic_guru modules
from google.adk.agents import Agent
from google.adk.tools import google_search

try:
    from carnatic_guru.config import DEFAULT_MODEL, RAGA_INFO_AGENT_INSTRUCTION
    from carnatic_guru.mcp_pdf_server import read_pdf_lesson, get_available_lessons
except ImportError:
    # Fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from carnatic_guru.config import DEFAULT_MODEL, RAGA_INFO_AGENT_INSTRUCTION
    from carnatic_guru.mcp_pdf_server import read_pdf_lesson, get_available_lessons


# This agent runs ONCE at the beginning to create the first draft.
raga_info_agent = Agent(
    name="RagaInfoAgent",
    model=DEFAULT_MODEL,
    description="Provides detailed information about Carnatic ragas.",
    instruction=RAGA_INFO_AGENT_INSTRUCTION,
    tools=[google_search],
    output_key="raga_info",  # Stores the first draft in the state.
)

root_agent = raga_info_agent