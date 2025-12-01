"""Basic Lesson Agent for CarnaticGuru AI.

Provides lessons from carnatic_basics.pdf using MCP server.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path BEFORE any imports of carnatic_guru
# This must happen before importing carnatic_guru modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import carnatic_guru modules
from google.adk.agents import Agent

try:
    from carnatic_guru.config import DEFAULT_MODEL, BASIC_LESSON_AGENT_INSTRUCTION
    from carnatic_guru.mcp_pdf_server import read_pdf_lesson, get_available_lessons
except ImportError:
    # If still failing, add current dir as fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from carnatic_guru.config import DEFAULT_MODEL, BASIC_LESSON_AGENT_INSTRUCTION
    from carnatic_guru.mcp_pdf_server import read_pdf_lesson, get_available_lessons

# Create the Agent
basic_lesson_agent = Agent(
    name="BasicLessonAgent",
    model=DEFAULT_MODEL,
    description="Provides Carnatic music lessons from PDF resources.",
    instruction=BASIC_LESSON_AGENT_INSTRUCTION,
    tools=[read_pdf_lesson],
)

root_agent = basic_lesson_agent
