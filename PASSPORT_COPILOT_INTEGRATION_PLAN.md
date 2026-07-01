# PlanCraft — Architecture & Integration Plan

## Executive Summary

**PlanCraft is an MCP server** — a VS Code Copilot agent (like Passport Copilot) that you interact with directly in Copilot Chat. Select "PlanCraft" from the agent dropdown and say *"Generate stories from this SOW for CITI D3"*.

**GitHub Copilot IS the LLM** — PlanCraft doesn't call OpenAI/Azure directly. It provides tools and structured context; Copilot handles all reasoning and story generation. Zero LLM cost, no API keys.

**Passport Copilot is a live dependency** — PlanCraft spawns the real Passport Copilot MCP server as a subprocess (stdio mode) and calls its 113 tools for domain knowledge. No mock agents. Real schema, real docs, real client customizations.

**Always client-specific** — User specifies a client (e.g., "CITI D3"). PlanCraft connects to that client's database via Passport Copilot, gets their exact Passport version, customizations, and business rules.

**Open plugin architecture** — Passport is the first real agent via MCP. T360, HighQ, or any future product can be added by pointing to another MCP server.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            VS Code + GitHub Copilot                           │
│                                                                              │
│   User: "Generate stories from this SOW for CITI D3"                         │
│                                                                              │
│   Copilot ←──→ PlanCraft Agent (MCP Server)                                 │
│                    │                                                         │
│                    │ @mcp.tool() handlers                                    │
│                    ├── parse_sow(file)                                        │
│                    ├── get_passport_context(client, sow_concepts)             │
│                    ├── detect_feature_overlap(concepts)                       │
│                    ├── generate_stories_context(sow + passport_context)       │
│                    ├── validate_stories(stories)                              │
│                    ├── list_available_agents()                                │
│                    └── export_to_jira(stories, project_key) [placeholder]     │
│                           │                                                  │
│                           │ MCP Client (stdio subprocess)                    │
│                           ▼                                                  │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │           Passport Copilot MCP Server (113 tools)                   │    │
│   │                                                                     │    │
│   │  passport_answer    schema_get_table     discover_customizations    │    │
│   │  search_passport_docs  smart_search      search_groovy_scripts      │    │
│   │  get_module_docs    table_dependencies   search_workflows           │    │
│   │  list_modules       impact_analysis      search_business_rules      │    │
│   │  db_connect_client  entity_context       generate_test_cases        │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: How This Differs from Passport Copilot

| Aspect | Passport Copilot | PlanCraft |
|--------|-----------------|-----------|
| **Purpose** | Dev assistant (code, debug, query) | Planning assistant (SOW → stories) |
| **LLM role** | Answers questions, generates code | Generates structured epics/stories/tasks |
| **Input** | Developer questions | SOW document + client name |
| **Output** | Code, explanations, query results | Jira-ready JSON (epics, features, stories, ACs) |
| **Passport knowledge** | Direct (has the knowledge) | Indirect (calls Passport Copilot for it) |
| **Agents** | Single product (Passport) | Multi-product orchestrator |

---

## How It Works — End to End

### User Interaction (in VS Code Copilot Chat)

```
User: [selects PlanCraft agent]
User: "Here's our SOW for CITI. Generate user stories."
      [attaches SOW.pdf or pastes text]

PlanCraft tools execute:
  1. parse_sow(file) → extracts text, identifies key concepts
  2. get_passport_context("CITI-D3", concepts) →
       - Calls Passport Copilot: db_connect_client("CITI-D3")
       - Calls: discover_customizations()
       - Calls: passport_answer(concept) for each concept
       - Calls: schema_search_tables(concept)
       - Calls: search_workflows(concept)
       - Returns: structured context blob
  3. detect_feature_overlap(concepts) →
       - Calls: search_passport_docs(concept)
       - Calls: search_passport_code(concept)
       - Returns: list of "this already exists" warnings
  4. Copilot uses all this context to generate stories
  5. validate_stories(stories) →
       - Calls: impact_analysis(entity) for risky changes
       - Calls: search_business_rules(entity)
       - Returns: validation issues

Copilot returns: Structured response with epics/stories/ACs + warnings
```

---

## PlanCraft MCP Server — Tool Design

### Tools Exposed to Copilot

| Tool | Description | Returns |
|------|-------------|---------|
| `parse_sow` | Parse uploaded SOW (PDF/DOCX/TXT), extract text + key concepts | `{text, concepts, entities, modules_mentioned}` |
| `get_passport_context` | Connect to client DB, gather full Passport context for planning | `{version, rules, existing_features, constraints, customizations, schema}` |
| `detect_feature_overlap` | Check which SOW requirements already exist in Passport | `[{concept, existing_impl, recommendation}]` |
| `generate_stories_context` | Build the complete prompt context (SOW + Passport knowledge) for Copilot | Structured text context that Copilot uses to generate stories |
| `validate_stories` | Validate generated stories against Passport rules + schema | `[{story, issue, severity}]` |
| `generate_test_cases` | Generate QA test cases for stories (delegates to Passport Copilot) | Test cases per story |
| `list_agents` | List available product agents | `[{name, description, status}]` |
| `export_jira` | Export stories to Jira (placeholder) | `{status, preview}` |

### Resources (browsable context for Copilot)

| Resource URI | Description |
|-------------|-------------|
| `plancraft://status` | Current state: connected client, agent, SOW loaded |
| `plancraft://last-context` | Last Passport context gathered (cacheable) |
| `plancraft://output-schema` | JSON schema for story output format |

---

## Passport Copilot Tools Used by PlanCraft

### Phase 1: Client Connection & Context

| Tool Called | Why |
|------------|-----|
| `db_list_clients` | Get list of available client databases |
| `db_connect_client(client_id)` | Connect + auto-detect Passport version |
| `discover_customizations(custom_only=False)` | Get ALL client customizations (Groovy, tables, columns) |
| `list_modules(with_versions=True)` | Know what modules client has |

### Phase 2: SOW Concept Analysis

| Tool Called | Why |
|------------|-----|
| `passport_answer(concept)` | Get domain knowledge about each SOW concept |
| `search_passport_docs(concept)` | Find existing feature docs that overlap |
| `smart_search(concept)` | Find schema tables related to SOW features |
| `schema_get_table(table)` | Get column details for relevant entities |
| `table_dependencies(table)` | Understand FK relationships |
| `entity_context(entity)` | Full entity relationship map |

### Phase 3: Existing Implementation Detection

| Tool Called | Why |
|------------|-----|
| `search_passport_code(concept)` | Find existing source code implementations |
| `search_groovy_scripts(concept)` | Find client-specific Groovy (commands, validators) |
| `search_workflows(concept)` | Find existing approval/status workflows |
| `search_screens(concept)` | Find existing UI screens |
| `search_business_rules(concept)` | Find validation rules |

### Phase 4: Validation

| Tool Called | Why |
|------------|-----|
| `impact_analysis(entity, "entity")` | Assess risk of proposed changes |
| `search_business_rules(entity)` | Check what rules would be affected |
| `generate_test_cases(requirement)` | Auto-generate test cases |

---

## Project Structure (Revised — No Mocks)

```
plancraft/
├── plancraft.agent.md              ← VS Code agent definition (like passport.agent.md)
├── src/
│   ├── app.py                      ← FastMCP server instance
│   ├── server.py                   ← Entry point (stdio mode)
│   ├── state.py                    ← Global state (connected client, cached context)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── sow_tools.py           ← parse_sow, extract concepts
│   │   ├── context_tools.py       ← get_passport_context, detect_overlap
│   │   ├── story_tools.py         ← generate_stories_context, validate_stories
│   │   ├── test_tools.py          ← generate_test_cases (delegates to Passport)
│   │   └── export_tools.py        ← export_jira (placeholder)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py          ← Abstract interface for product agents
│   │   ├── registry.py            ← Agent discovery + management
│   │   └── passport_mcp_agent.py  ← Real agent: MCP client → Passport Copilot
│   ├── services/
│   │   ├── sow_parser.py          ← PDF/DOCX/TXT extraction
│   │   ├── concept_extractor.py   ← NLP-lite: extract entities, modules, operations
│   │   └── jira_service.py        ← Jira REST API (placeholder)
│   ├── resources/
│   │   └── resources.py           ← MCP resources (status, schema, last-context)
│   └── config/
│       └── settings.py            ← Paths, agent configs
├── requirements.txt
├── .env.example
└── README.md
```

---

## Key Design Decisions

### 1. PlanCraft is an MCP Server (Not a FastAPI App)

Like Passport Copilot, PlanCraft registers as a VS Code Copilot agent via `plancraft.agent.md`. It exposes `@mcp.tool()` handlers that Copilot calls. **Copilot is the LLM** — it uses PlanCraft's tool outputs as context to generate stories.

```python
# src/app.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="plancraft",
    instructions=(
        "You are PlanCraft — an AI planning agent that generates structured development plans "
        "from Statement of Work documents. ALWAYS call get_passport_context first with the "
        "client name. Then use the context to generate Epics, Features, User Stories with "
        "Acceptance Criteria, Tasks, and Story Points. Output Jira-ready JSON."
    ),
)
```

### 2. Passport Copilot as Subprocess (stdio)

PlanCraft spawns Passport Copilot as a child process and communicates via MCP protocol over stdin/stdout:

```python
# src/agents/passport_mcp_agent.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PASSPORT_PYTHON = r"C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\.venv\Scripts\python.exe"
PASSPORT_SERVER = r"C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\src\server.py"

class PassportMCPAgent:
    async def connect(self):
        server_params = StdioServerParameters(
            command=PASSPORT_PYTHON,
            args=[PASSPORT_SERVER],
        )
        read, write = await stdio_client(server_params).__aenter__()
        self.session = ClientSession(read, write)
        await self.session.initialize()

    async def call_tool(self, name: str, args: dict) -> str:
        result = await self.session.call_tool(name, args)
        return result.content[0].text
```

### 3. Copilot Generates Stories (Not PlanCraft)

PlanCraft does NOT have a story_generator that calls an LLM. Instead, it provides **rich context** as tool responses, and Copilot's LLM generates the stories. The `generate_stories_context` tool returns a formatted prompt context that guides Copilot:

```python
@mcp.tool()
async def generate_stories_context(sow_text: str, passport_context: dict) -> str:
    """Build complete context for story generation. Copilot uses this to write stories."""
    return f"""
## SOW Summary
{sow_text[:3000]}

## Passport Product Context (Client: {passport_context['client']}, Version: {passport_context['version']})

### Existing Features (DO NOT duplicate these):
{format_list(passport_context['existing_features'])}

### Business Rules:
{format_list(passport_context['rules'])}

### Constraints:
{format_list(passport_context['constraints'])}

### Client Customizations Already In Place:
{format_list(passport_context['customizations'])}

### Schema Context:
{format_list(passport_context['schema'])}

## OUTPUT REQUIREMENTS
Generate Jira-ready JSON with this structure:
- Epics > Features > User Stories > Acceptance Criteria > Tasks
- Each story: "As a [role], I want [goal], so that [benefit]"
- ACs in Given/When/Then format
- Story points: 1, 2, 3, 5, 8, 13
- Priority: Critical, High, Medium, Low
- Flag any stories that overlap with existing features
"""
```

### 4. No Mock Agents

The old mock agents (`passport_agent.py`, `t360_agent.py` with hardcoded data) are removed. The `PassportMCPAgent` calls the real server. For T360 or future products, someone would:
1. Build a T360 MCP server (like Passport Copilot was built)
2. Add a `T360MCPAgent` pointing to that server
3. Register it in the agent registry

### 5. SOW File Support

All formats: PDF, DOCX, plain text. The `parse_sow` tool handles extraction and also does concept extraction (finds Passport entity names, module names, operation types mentioned in the SOW).

---

## Agent Definition File

```yaml
# plancraft.agent.md
---
name: PlanCraft
description: AI planning agent — generates structured development plans from SOW documents
tools:
  - plancraft/parse_sow
  - plancraft/get_passport_context
  - plancraft/detect_feature_overlap
  - plancraft/generate_stories_context
  - plancraft/validate_stories
  - plancraft/generate_test_cases
  - plancraft/list_agents
  - plancraft/export_jira
  - read/readFile
  - search/codebase
---

# PlanCraft

You are **PlanCraft**, an AI planning agent that converts Statements of Work into structured, Jira-ready development plans.

## MANDATORY WORKFLOW

1. **Parse the SOW**: Call `parse_sow` with the uploaded file or pasted text
2. **Get Passport Context**: Call `get_passport_context` with the client name and extracted concepts
3. **Detect Overlap**: Call `detect_feature_overlap` to find what already exists
4. **Generate Stories**: Use the context from above to generate structured stories in JSON format
5. **Validate**: Call `validate_stories` to check for conflicts/risks

## OUTPUT FORMAT

Always output stories as structured JSON:
```json
{
  "epics": [{
    "title": "...",
    "features": [{
      "title": "...",
      "user_stories": [{
        "title": "As a [role], I want [goal], so that [benefit]",
        "acceptance_criteria": ["Given... When... Then..."],
        "tasks": ["..."],
        "priority": "High",
        "story_points": 5
      }]
    }]
  }],
  "warnings": ["Existing feature overlap detected: ..."],
  "assumptions": ["..."]
}
```
```

---

## Implementation Order

| Phase | What | Effort |
|-------|------|--------|
| **1** | PlanCraft MCP server skeleton (`app.py`, `server.py`, agent definition) | 1 day |
| **2** | SOW parser tool (PDF/DOCX/TXT + concept extraction) | 1 day |
| **3** | Passport MCP client (`PassportMCPAgent` — connect, call tools) | 1 day |
| **4** | Context tools (`get_passport_context`, `detect_feature_overlap`) | 1-2 days |
| **5** | Story context tool + validation tool | 1 day |
| **6** | Test in Copilot Chat end-to-end | 1 day |
| **7** | Jira export (placeholder → real) | Later |
| **8** | T360 agent (when T360 MCP server exists) | Later |

---

## Configuration

```env
# .env
PASSPORT_MCP_PYTHON=C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\.venv\Scripts\python.exe
PASSPORT_MCP_SERVER=C:\PassportCopilot\clients\DevTools\Passport-Copilot-MCP\src\server.py
```

---

## VS Code Setup (for the user)

1. Copy `plancraft.agent.md` to the workspace root (or VS Code prompts folder)
2. Add MCP server config to VS Code settings:

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

3. Open Copilot Chat → select **PlanCraft** from agent dropdown
4. Say: *"Generate stories from this SOW for CITI D3"*

---

## What Changes From Current Code

| Current (in `c:\Code Games 2026\plancraft\`) | New |
|----------------------------------------------|-----|
| FastAPI app (`app.py`) | FastMCP server (`src/app.py`) |
| Mock `passport_agent.py` with hardcoded data | `PassportMCPAgent` calling real server |
| Mock `t360_agent.py` with hardcoded data | Removed (add when T360 MCP exists) |
| `story_generator.py` calling OpenAI API | Removed — Copilot IS the LLM |
| `services/orchestrator.py` pipeline | Replaced by MCP tools that Copilot calls |
| Frontend upload UI (planned) | Not needed — Copilot Chat IS the UI |
| REST API endpoints (`/generate`) | Not needed — MCP tools are the API |

---

## Summary: Why This Is Better

| Old Approach | New Approach |
|-------------|--------------|
| Build custom backend + frontend | Copilot Chat is the UI |
| Pay for OpenAI API calls | Copilot subscription (already have) |
| Mock Passport knowledge | Real 88K-doc knowledge base |
| Hardcoded business rules | Live client-specific rules from DB |
| Build story generation logic | Copilot's LLM generates stories |
| Maintain two separate systems | Single agent in the same IDE |
| Deploy a web service | Just run a Python script |

**Net result:** ~80% less code to write. The heavy lifting (LLM reasoning, Passport knowledge) is already built. PlanCraft is the thin orchestration layer that connects them.
