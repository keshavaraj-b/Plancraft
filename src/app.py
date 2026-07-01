"""
PlanCraft MCP Server — main application instance.

This is the FastMCP server that VS Code Copilot connects to.
All tools are registered here via imports from the tools/ package.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="plancraft",
    instructions=(
        "You are PlanCraft — an AI planning agent that generates structured development plans "
        "from Statement of Work (SOW) documents. You work with domain-specific product agents "
        "(like Passport Copilot) to understand the target platform before generating stories.\n\n"
        "MANDATORY WORKFLOW:\n"
        "1. Call parse_sow to extract text and concepts from the SOW document\n"
        "2. Call get_passport_context with the client name and extracted concepts\n"
        "3. Call detect_feature_overlap to find what already exists in the platform\n"
        "4. Use the gathered context to generate structured Epics > Features > User Stories\n"
        "5. Call validate_stories to check for risks and conflicts\n\n"
        "OUTPUT FORMAT: Always produce Jira-ready JSON with epics, features, user stories "
        "(As a [role], I want [goal], so that [benefit]), acceptance criteria (Given/When/Then), "
        "tasks, story points (1,2,3,5,8,13), and priority (Critical/High/Medium/Low)."
    ),
)

# Register all tools by importing the tool modules
from src.tools import sow_tools  # noqa: E402, F401
from src.tools import context_tools  # noqa: E402, F401
from src.tools import story_tools  # noqa: E402, F401
from src.tools import export_tools  # noqa: E402, F401
from src.resources import resources  # noqa: E402, F401
