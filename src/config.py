"""
PlanCraft configuration — paths and settings.
"""

import os
from pathlib import Path

# Passport Copilot MCP server paths (configurable via env vars)
PASSPORT_MCP_PYTHON = os.environ.get(
    "PASSPORT_MCP_PYTHON",
    r"C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\.venv\Scripts\python.exe",
)

PASSPORT_MCP_SERVER = os.environ.get(
    "PASSPORT_MCP_SERVER",
    r"C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\src\server.py",
)

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
