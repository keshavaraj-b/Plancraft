# PlanCraft

**AI planning agent that generates structured user stories from SOW documents.**

PlanCraft is an MCP server — a VS Code Copilot agent you interact with directly in Copilot Chat. It connects to the real Passport Copilot MCP server to get domain knowledge, then helps you generate Jira-ready development plans.

## How It Works

1. You select **PlanCraft** in Copilot Chat
2. Paste or attach your SOW document
3. PlanCraft parses the SOW, connects to your client's Passport instance
4. Gathers domain knowledge (modules, schema, customizations, existing features)
5. Copilot generates structured epics/features/stories using the context
6. Stories are validated against Passport rules and impact analysis

**GitHub Copilot IS the LLM** — no OpenAI API keys needed.

## Setup

### Prerequisites

- VS Code with GitHub Copilot
- Python 3.11+
- Passport Copilot MCP server installed locally

### Install

```bash
cd plancraft
pip install -r requirements.txt
```

### Configure VS Code

Add to your VS Code settings (`.vscode/settings.json` or User settings):

```json
{
  "mcp": {
    "servers": {
      "plancraft": {
        "command": "python",
        "args": ["c:/Code Games 2026/plancraft/src/server.py"]
      }
    }
  }
}
```

### Environment

Copy `.env.example` to `.env` and update the Passport Copilot paths if needed:

```bash
cp .env.example .env
```

## Usage

1. Open Copilot Chat in VS Code
2. Select **PlanCraft** from the agent dropdown
3. Say: _"Generate stories from this SOW for CITI-D3"_
4. Attach or paste your SOW document

## Project Structure

```
plancraft/
├── plancraft.agent.md          ← VS Code agent definition
├── src/
│   ├── app.py                  ← FastMCP server instance
│   ├── server.py               ← Entry point (stdio mode)
│   ├── state.py                ← Session state
│   ├── config.py               ← Configuration
│   ├── tools/
│   │   ├── sow_tools.py       ← parse_sow
│   │   ├── context_tools.py   ← get_passport_context, detect_feature_overlap
│   │   ├── story_tools.py     ← generate_stories_context, validate_stories
│   │   └── export_tools.py    ← export_jira (placeholder)
│   ├── agents/
│   │   └── passport_mcp_agent.py  ← Real MCP client to Passport Copilot
│   └── resources/
│       └── resources.py        ← MCP resources (status, schema)
├── requirements.txt
├── .env.example
└── PASSPORT_COPILOT_INTEGRATION_PLAN.md
```

## Tools

| Tool | Description |
|------|-------------|
| `parse_sow` | Parse SOW document (PDF/DOCX/TXT) and extract concepts |
| `get_passport_context` | Connect to client, gather Passport domain knowledge |
| `detect_feature_overlap` | Find SOW requirements that already exist in Passport |
| `generate_stories_context` | Build complete context for story generation |
| `validate_stories` | Validate stories against Passport rules |
| `list_agents` | List available product agents |
| `export_jira` | Preview Jira export (placeholder) |

## Architecture

PlanCraft spawns Passport Copilot as a subprocess (stdio MCP protocol) and calls its 113 tools for domain knowledge. Copilot handles all LLM reasoning — PlanCraft just provides tools and context.

## Adding New Product Agents

PlanCraft is open-source and extensible. To add a new product (e.g., T360, HighQ):

1. Build an MCP server for that product (like Passport Copilot)
2. Create a new agent class in `src/agents/` that connects to it
3. Register its tools in `src/tools/`
4. The agent becomes available via `list_agents`
