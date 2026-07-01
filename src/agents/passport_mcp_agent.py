"""
Passport MCP Agent — connects to the real Passport Copilot MCP server
via stdio subprocess and calls its tools for domain knowledge.
"""

import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.config import PASSPORT_MCP_PYTHON, PASSPORT_MCP_SERVER

logger = logging.getLogger(__name__)


class PassportMCPAgent:
    """
    MCP client that spawns Passport Copilot as a subprocess and calls its tools.

    Usage:
        agent = PassportMCPAgent()
        async with agent:
            result = await agent.call_tool("db_connect_client", {"client_id": "CITI-D3"})
    """

    def __init__(self):
        self._session: ClientSession | None = None
        self._stdio_context = None
        self._session_context = None

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

    async def connect(self):
        """Spawn Passport Copilot MCP server and establish session."""
        if self._session is not None:
            return

        server_params = StdioServerParameters(
            command=PASSPORT_MCP_PYTHON,
            args=[PASSPORT_MCP_SERVER],
        )

        logger.info("Spawning Passport Copilot MCP server...")
        self._stdio_context = stdio_client(server_params)
        read, write = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read, write)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()
        logger.info("Passport Copilot MCP session established.")

    async def disconnect(self):
        """Close the MCP session and kill the subprocess."""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
            self._session_context = None
            self._session = None
        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
            self._stdio_context = None
        logger.info("Passport Copilot disconnected.")

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        """
        Call a tool on the Passport Copilot MCP server.

        Args:
            name: Tool name (e.g., "passport_answer", "db_connect_client")
            arguments: Tool arguments dict

        Returns:
            Text content from the tool response.
        """
        if not self._session:
            raise RuntimeError("Not connected to Passport Copilot. Call connect() first.")

        logger.info(f"Calling Passport Copilot tool: {name}")
        result = await self._session.call_tool(name, arguments or {})

        # Extract text from result content
        if result.content:
            # MCP tool results can have multiple content blocks
            texts = []
            for block in result.content:
                if hasattr(block, "text"):
                    texts.append(block.text)
            return "\n".join(texts)
        return ""

    async def list_tools(self) -> list[dict]:
        """List all available tools on the Passport Copilot server."""
        if not self._session:
            raise RuntimeError("Not connected to Passport Copilot. Call connect() first.")

        tools_result = await self._session.list_tools()
        return [
            {"name": t.name, "description": t.description}
            for t in tools_result.tools
        ]


# Singleton instance — reused across tool calls within a session
_passport_agent: PassportMCPAgent | None = None


async def get_passport_agent() -> PassportMCPAgent:
    """Get or create the singleton Passport MCP agent."""
    global _passport_agent
    if _passport_agent is None or not _passport_agent.is_connected:
        _passport_agent = PassportMCPAgent()
        await _passport_agent.connect()
    return _passport_agent
