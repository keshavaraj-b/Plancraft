"""
PlanCraft global state — tracks current session context.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanCraftState:
    """Mutable session state for the current PlanCraft interaction."""

    connected_client: str | None = None
    passport_connected: bool = False
    passport_version: str | None = None
    last_sow_text: str | None = None
    last_concepts: list[str] = field(default_factory=list)
    last_context: dict[str, Any] = field(default_factory=dict)
    last_stories: list[dict] = field(default_factory=list)


# Singleton state instance
state = PlanCraftState()
