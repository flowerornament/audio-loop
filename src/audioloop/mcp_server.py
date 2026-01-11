"""MCP server for audioloop CLI tools.

Exposes audioloop analysis and rendering capabilities as MCP tools.
Uses FastMCP for automatic schema generation and protocol handling.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from audioloop import __version__

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("audioloop.mcp")


async def run_cli(args: list[str]) -> str:
    """Run audioloop CLI command asynchronously.

    Args:
        args: Command arguments to pass to audioloop CLI.

    Returns:
        stdout from the command.

    Raises:
        RuntimeError: If command fails with non-zero exit code.
    """
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "audioloop",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        raise RuntimeError(f"audioloop failed: {error_msg}")

    return stdout.decode()


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Verify audioloop CLI is available on startup."""
    logger.info("Starting audioloop MCP server...")

    # Verify audioloop is installed and accessible
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "audioloop",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError("audioloop CLI not available")

        version = stdout.decode().strip()
        logger.info(f"audioloop CLI ready: {version}")
    except FileNotFoundError:
        raise RuntimeError("Python executable not found")

    yield

    logger.info("Shutting down audioloop MCP server")


# Create FastMCP server instance
mcp = FastMCP("audioloop", lifespan=app_lifespan)


@mcp.tool()
async def version() -> dict:
    """Get audioloop version information.

    Returns:
        Version info including audioloop and MCP server versions.
    """
    return {
        "audioloop": __version__,
        "mcp_server": "0.1.0",
        "status": "ready",
    }


if __name__ == "__main__":
    mcp.run()
