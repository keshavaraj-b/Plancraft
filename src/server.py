"""
PlanCraft MCP Server — entry point.

Run with:
  python src/server.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' package resolves
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app import mcp  # noqa: E402


def main():
    """Start PlanCraft MCP server in stdio mode."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
