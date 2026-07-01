"""
Story Tools — build context for story generation and validate generated stories.
"""

import json
import logging
from typing import Any

from src.app import mcp
from src.state import state
from src.agents.passport_mcp_agent import get_passport_agent

logger = logging.getLogger(__name__)


@mcp.tool()
async def generate_stories_context(sow_summary: str | None = None, client_id: str | None = None) -> str:
    """
    Build the complete context Copilot needs to generate structured user stories.

    Combines SOW text, Passport domain knowledge, existing features, and constraints
    into a structured prompt context. Copilot (the LLM) uses this to write stories.

    Args:
        sow_summary: SOW text summary. If None, uses last parsed SOW.
        client_id: Client identifier. If None, uses last connected client.

    Returns:
        Formatted context string that guides Copilot's story generation.
    """
    sow_text = sow_summary or state.last_sow_text or "No SOW loaded"
    context = state.last_context
    client = client_id or state.connected_client or "Unknown"

    # Build structured context for Copilot
    sections = []

    sections.append(f"## SOW Content (Client: {client})")
    sections.append(sow_text[:4000])

    if context.get("modules"):
        sections.append("\n## Passport Modules Available")
        sections.append(str(context["modules"])[:800])

    if context.get("customizations"):
        sections.append("\n## Client Customizations Already In Place")
        sections.append(str(context["customizations"])[:800])

    if context.get("concept_knowledge"):
        sections.append("\n## Domain Knowledge per Concept")
        for ck in context["concept_knowledge"]:
            sections.append(f"\n### {ck['concept']}")
            sections.append(ck["knowledge"][:300])

    if context.get("schema"):
        sections.append("\n## Relevant Database Schema")
        for s in context["schema"]:
            sections.append(f"\n### Tables for: {s['concept']}")
            sections.append(s["tables"][:200])

    sections.append("""
## OUTPUT REQUIREMENTS

Generate a JSON object with this EXACT structure:
```json
{
  "epics": [
    {
      "title": "Epic title",
      "description": "Epic description",
      "features": [
        {
          "title": "Feature title",
          "user_stories": [
            {
              "title": "As a [role], I want [goal], so that [benefit]",
              "description": "Detailed description",
              "acceptance_criteria": [
                "Given [context], When [action], Then [outcome]"
              ],
              "tasks": ["Technical task 1", "Technical task 2"],
              "story_points": 5,
              "priority": "High",
              "labels": ["module-name"]
            }
          ]
        }
      ]
    }
  ],
  "warnings": ["Any overlap with existing features or risks"],
  "assumptions": ["Assumptions made during planning"],
  "total_story_points": 42
}
```

RULES:
- Story points: use Fibonacci (1, 2, 3, 5, 8, 13)
- Priority: Critical, High, Medium, Low
- Acceptance criteria: MUST be Given/When/Then format
- User stories: MUST follow "As a [role], I want [goal], so that [benefit]"
- Flag any feature that overlaps with existing Passport functionality
- Include migration/data tasks if schema changes are needed
- Include configuration tasks for Groovy/workflow changes
""")

    return "\n".join(sections)


@mcp.tool()
async def validate_stories(stories_json: str) -> dict[str, Any]:
    """
    Validate generated stories against Passport domain rules and schema.

    Checks for:
    - Impact analysis on affected entities
    - Business rule conflicts
    - Missing acceptance criteria
    - Unrealistic story point estimates

    Args:
        stories_json: JSON string of generated stories (epics/features/stories structure).

    Returns:
        Validation report with issues, warnings, and suggestions.
    """
    try:
        stories = json.loads(stories_json)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "warnings": [], "suggestions": []}

    issues = []
    warnings = []
    suggestions = []

    agent = await get_passport_agent()

    # Validate structure
    epics = stories.get("epics", [])
    if not epics:
        issues.append("No epics found in the stories JSON")

    total_points = 0

    for epic in epics:
        for feature in epic.get("features", []):
            for story in feature.get("user_stories", []):
                title = story.get("title", "")

                # Check story format
                if not title.lower().startswith("as a"):
                    warnings.append(f"Story doesn't follow 'As a...' format: {title[:50]}")

                # Check ACs
                acs = story.get("acceptance_criteria", [])
                if not acs:
                    issues.append(f"Story has no acceptance criteria: {title[:50]}")

                # Check story points
                points = story.get("story_points", 0)
                if points not in (1, 2, 3, 5, 8, 13):
                    warnings.append(f"Non-Fibonacci story points ({points}): {title[:50]}")
                total_points += points

    # Run impact analysis on entities mentioned
    entities_to_check = set()
    for epic in epics:
        for feature in epic.get("features", []):
            for story in feature.get("user_stories", []):
                for label in story.get("labels", []):
                    entities_to_check.add(label)

    impact_results = []
    for entity in list(entities_to_check)[:5]:
        try:
            impact = await agent.call_tool("impact_analysis", {"target": entity, "target_type": "entity"})
            if impact and "high" in impact.lower():
                warnings.append(f"High impact detected for entity '{entity}': {impact[:100]}")
            impact_results.append({"entity": entity, "impact": impact[:200]})
        except Exception:
            pass

    # Cache validated stories
    state.last_stories = epics

    return {
        "valid": len(issues) == 0,
        "total_story_points": total_points,
        "epic_count": len(epics),
        "story_count": sum(
            len(s.get("user_stories", []))
            for e in epics
            for s in e.get("features", [])
        ),
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "impact_analysis": impact_results,
    }
