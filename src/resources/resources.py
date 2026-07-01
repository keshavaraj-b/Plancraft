"""
MCP Resources — browsable context for Copilot.
"""

import json

from src.app import mcp
from src.state import state


@mcp.resource("plancraft://status")
async def get_status() -> str:
    """Current PlanCraft session status."""
    return json.dumps({
        "connected_client": state.connected_client,
        "passport_connected": state.passport_connected,
        "passport_version": state.passport_version,
        "sow_loaded": state.last_sow_text is not None,
        "concepts_extracted": len(state.last_concepts),
        "stories_generated": len(state.last_stories),
    }, indent=2)


@mcp.resource("plancraft://output-schema")
async def get_output_schema() -> str:
    """JSON schema for the story output format."""
    schema = {
        "type": "object",
        "properties": {
            "epics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "features": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "user_stories": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "title": {"type": "string", "pattern": "^As a .+"},
                                                "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                                                "tasks": {"type": "array", "items": {"type": "string"}},
                                                "story_points": {"type": "integer", "enum": [1, 2, 3, 5, 8, 13]},
                                                "priority": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
                                                "labels": {"type": "array", "items": {"type": "string"}},
                                            },
                                            "required": ["title", "acceptance_criteria", "story_points", "priority"],
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "total_story_points": {"type": "integer"},
        },
    }
    return json.dumps(schema, indent=2)
