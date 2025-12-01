import sys
import os
from pathlib import Path

# Add parent directory to path BEFORE any imports of carnatic_guru
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import carnatic_guru modules
from google.adk.agents import Agent
from google.adk.tools import AgentTool


try:
    from carnatic_guru.config import DEFAULT_MODEL, ORCHESTRATOR_AGENT_INSTRUCTION
    from carnatic_guru.basic_lesson_agent.agent import basic_lesson_agent
    from carnatic_guru.raga_info_agent.agent import raga_info_agent
    from carnatic_guru.swara_pattern_agent.agent import swara_pattern_agent
except ImportError:
    # Fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from carnatic_guru.config import DEFAULT_MODEL, ORCHESTRATOR_AGENT_INSTRUCTION
    from carnatic_guru.basic_lesson_agent.agent import basic_lesson_agent
    from carnatic_guru.raga_info_agent.agent import raga_info_agent
    from carnatic_guru.swara_pattern_agent.agent import swara_pattern_agent


orchestrator_agent = Agent(
    name="orchestrator_agent",
    model=DEFAULT_MODEL,
    description="A carnatic guru that Routes all student requests to learning agents.",
    instruction=ORCHESTRATOR_AGENT_INSTRUCTION,
    tools=[AgentTool(basic_lesson_agent), AgentTool(raga_info_agent), AgentTool(swara_pattern_agent)],
)

root_agent = orchestrator_agent