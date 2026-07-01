"""
Context Tools — gather domain knowledge from Passport Copilot for story generation.
"""

import logging
from typing import Any

from src.app import mcp
from src.state import state
from src.agents.passport_mcp_agent import get_passport_agent

logger = logging.getLogger(__name__)


@mcp.tool()
async def get_passport_context(client_id: str, concepts: list[str] | None = None) -> dict[str, Any]:
    """
    Connect to a Passport client and gather full domain context for planning.

    This calls multiple Passport Copilot tools to build a complete picture:
    - Connects to the client database
    - Gets client's Passport version and modules
    - Discovers existing customizations
    - Queries domain knowledge for each SOW concept

    Args:
        client_id: Client database identifier (e.g., "CITI-D3", "AMEX-P1")
        concepts: Key concepts from the SOW to research. If None, uses last parsed SOW concepts.

    Returns:
        Comprehensive context dict with version, modules, customizations,
        existing features, business rules, and schema info.
    """
    if concepts is None:
        concepts = state.last_concepts

    agent = await get_passport_agent()

    # Step 1: Connect to client
    logger.info(f"Connecting to client: {client_id}")
    connect_result = await agent.call_tool("db_connect_client", {"client_id": client_id})

    state.connected_client = client_id
    state.passport_connected = True

    # Step 2: Get modules and version info
    modules_result = await agent.call_tool("list_modules", {"with_versions": True})

    # Step 3: Discover customizations
    customizations = await agent.call_tool("discover_customizations", {"custom_only": False})

    # Step 4: Research each concept
    concept_knowledge = []
    for concept in concepts[:10]:  # Limit to 10 concepts to avoid timeout
        try:
            answer = await agent.call_tool("passport_answer", {"question": concept})
            concept_knowledge.append({"concept": concept, "knowledge": answer[:500]})
        except Exception as e:
            logger.warning(f"Failed to get knowledge for concept '{concept}': {e}")
            concept_knowledge.append({"concept": concept, "knowledge": f"Error: {e}"})

    # Step 5: Schema search for key concepts
    schema_info = []
    for concept in concepts[:5]:
        try:
            tables = await agent.call_tool("smart_search", {"query": concept})
            schema_info.append({"concept": concept, "tables": tables[:300]})
        except Exception as e:
            logger.warning(f"Schema search failed for '{concept}': {e}")

    context = {
        "client": client_id,
        "connection": connect_result[:200],
        "modules": modules_result[:1000],
        "customizations": customizations[:1000],
        "concept_knowledge": concept_knowledge,
        "schema": schema_info,
    }

    # Cache in state
    state.last_context = context

    return context


@mcp.tool()
async def detect_feature_overlap(concepts: list[str] | None = None) -> list[dict]:
    """
    Check which SOW requirements already exist in Passport.

    Searches docs, code, workflows, and screens for each concept to identify
    features that are already built (avoid duplicating effort in stories).

    Args:
        concepts: List of feature concepts to check. If None, uses last parsed SOW concepts.

    Returns:
        List of overlap findings with concept, existing implementation details,
        and recommendation (skip, extend, or customize).
    """
    if concepts is None:
        concepts = state.last_concepts

    agent = await get_passport_agent()
    overlaps = []

    for concept in concepts[:10]:
        finding = {"concept": concept, "existing_implementations": [], "recommendation": "new"}

        # Search docs
        try:
            docs = await agent.call_tool("search_passport_docs", {"query": concept})
            if docs and "no results" not in docs.lower():
                finding["existing_implementations"].append({"type": "docs", "summary": docs[:200]})
        except Exception:
            pass

        # Search workflows
        try:
            workflows = await agent.call_tool("search_workflows", {"query": concept})
            if workflows and "no results" not in workflows.lower():
                finding["existing_implementations"].append({"type": "workflow", "summary": workflows[:200]})
        except Exception:
            pass

        # Search code
        try:
            code = await agent.call_tool("search_passport_code", {"query": concept})
            if code and "no results" not in code.lower():
                finding["existing_implementations"].append({"type": "code", "summary": code[:200]})
        except Exception:
            pass

        # Determine recommendation
        impl_count = len(finding["existing_implementations"])
        if impl_count >= 2:
            finding["recommendation"] = "skip_or_extend"
        elif impl_count == 1:
            finding["recommendation"] = "extend_or_customize"
        else:
            finding["recommendation"] = "new_development"

        overlaps.append(finding)

    return overlaps


@mcp.tool()
async def list_agents() -> list[dict]:
    """
    List all available product agents and their connection status.

    Returns:
        List of agents with name, description, and status.
    """
    agents = [
        {
            "name": "passport",
            "description": "Passport Legal Operations Platform — 113 tools, 88K docs, 73 modules",
            "status": "connected" if state.passport_connected else "available",
            "client": state.connected_client,
        },
        {
            "name": "t360",
            "description": "TeamConnect 360 (Future — requires T360 MCP server)",
            "status": "not_available",
            "client": None,
        },
    ]
    return agents
