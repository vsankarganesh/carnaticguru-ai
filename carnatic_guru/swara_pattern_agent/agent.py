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
    from carnatic_guru.config import DEFAULT_MODEL, SWARA_PATTERN_AGENT_INSTRUCTION
    from carnatic_guru.raga_info_agent import raga_info_agent
except ImportError:
    # Fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from carnatic_guru.config import DEFAULT_MODEL, SWARA_PATTERN_AGENT_INSTRUCTION
    from carnatic_guru.raga_info_agent import raga_info_agent

import random
# ---------------------------------------------------------
#  Utility — generate swara patterns
# ---------------------------------------------------------

def generate_swara_patterns(notes, pattern_lengths=[5, 6, 7, 8]):
    """
    Generate random swara patterns using the given raga notes.
    """

    # clean and dedupe notes
    notes = list(dict.fromkeys(notes))

    patterns = {}

    for length in pattern_lengths:

        # avoid mutating the original notes list
        temp = notes[:]

        if len(temp) >= length:
            random.shuffle(temp)
            pattern = temp[:length]
        else:
            expanded = []
            while len(expanded) < length:
                chunk = temp[:]
                random.shuffle(chunk)
                expanded.extend(chunk)
            pattern = expanded[:length]

        patterns[str(length)] = " ".join(pattern)

    return patterns


# ---------------------------------------------------------
#  Swara Pattern Agent (Main)
# ---------------------------------------------------------

class SwaraPatternAgentClass(Agent):
    """
    Custom Swara Pattern Agent with callback support
    """

    def run(self, prompt):
        """
        Orchestrator will send:
        {
           "raga": "Mayamalavagowla"
        }
        """

        raga = prompt.get("raga")
        if not raga:
            return "Error: Missing raga name."

        # TOOL CALL → RagaInfoAgent
        return {
            "tool": "RagaInfoAgent",
            "tool_input": {
                "query": raga,
                "mode": "swara_pattern"
            },
            "callback": "process_raga_info"
        }

    # ---------------------------------------------------------
    # Callback called after RagaInfoAgent returns
    # ---------------------------------------------------------
    def process_raga_info(self, tool_result):

        aro = tool_result.get("arohanam", [])
        ava = tool_result.get("avarohanam", [])

        if not aro or not ava:
            return "Raga information incomplete."

        # merge & dedupe notes
        notes = list(dict.fromkeys(aro + ava))

        # generate patterns
        patterns = generate_swara_patterns(notes)

        # plain output only
        output = []
        for count in ["5", "6", "7", "8"]:
            output.append(f"{count}-swars: {patterns[count]}")

        return "\n".join(output)



# ---------------------------------------------------------
#  Construct the ADK Agent
# ---------------------------------------------------------

swara_pattern_agent = SwaraPatternAgentClass(
    name="SwaraPatternAgent",
    model=DEFAULT_MODEL,
    description="Provides Swara practice patterns for any raga.",
    instruction=SWARA_PATTERN_AGENT_INSTRUCTION,
    tools=[
        AgentTool(
            raga_info_agent,
        )
    ],
)

root_agent = swara_pattern_agent