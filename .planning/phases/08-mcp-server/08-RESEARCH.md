# Phase 8: MCP Server - Research

**Researched:** 2026-01-11
**Domain:** Python MCP Server wrapping audioloop CLI
**Confidence:** HIGH

<research_summary>
## Summary

Researched the MCP (Model Context Protocol) Python SDK for building a server that wraps the audioloop CLI. The standard approach uses the official `mcp` package with the FastMCP high-level API, which provides decorator-based tool definitions, automatic schema generation from type hints, and built-in stdio transport.

Key finding: FastMCP handles all protocol complexity (JSON-RPC, transport, lifecycle). Tools are defined with simple decorators and Python type hints - the SDK generates JSON schemas automatically. For returning spectrograms (images), use the `Image` utility class. Use `subprocess.run()` or `asyncio.subprocess` to call the CLI, but ensure all output goes to stderr (not stdout, which is reserved for protocol).

**Primary recommendation:** Use official `mcp>=1.25.0` with FastMCP decorators. One tool per CLI command (render, analyze, iterate, compare, play). Return structured Pydantic models for JSON output. Use `Image` class for spectrogram PNG data.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp | >=1.25.0 | MCP Python SDK | Official Anthropic SDK, FastMCP included |
| pydantic | >=2.0 | Schema validation | Automatic JSON schema generation from models |
| asyncio | stdlib | Async subprocess | Non-blocking CLI execution |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=7.0 | Testing | Required for MCP server testing |
| inline-snapshot | >=0.7 | Snapshot testing | Recommended by MCP SDK docs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastMCP | Low-level Server | Low-level gives more control but FastMCP handles 99% of cases |
| Pydantic | TypedDict | TypedDict simpler but no validation, less rich schemas |
| asyncio subprocess | subprocess.run | sync is simpler if tools don't need concurrency |

**Installation:**
```bash
pip install "mcp[cli]>=1.25.0" pydantic pytest inline-snapshot
# or with uv
uv add "mcp[cli]>=1.25.0" pydantic pytest inline-snapshot
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/audioloop/
├── mcp_server.py         # FastMCP server with tool definitions
├── mcp_models.py         # Pydantic models for tool I/O schemas
└── (existing modules)    # cli.py, analyze.py, render.py, etc.
```

### Pattern 1: FastMCP Tool Definition
**What:** Use `@mcp.tool()` decorator with type hints for automatic schema generation
**When to use:** All tool definitions
**Example:**
```python
# Source: MCP Python SDK docs
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("audioloop", json_response=True)

class AnalysisResult(BaseModel):
    """Acoustic analysis of audio file."""
    file: str
    duration_sec: float
    spectral: dict
    temporal: dict

@mcp.tool()
async def analyze(
    file_path: str,
    no_psychoacoustic: bool = False,
    spectrogram: str | None = None
) -> AnalysisResult:
    """Analyze audio file and return acoustic measurements.

    Args:
        file_path: Path to WAV file to analyze
        no_psychoacoustic: Skip psychoacoustic metrics for faster analysis
        spectrogram: Optional path to save spectrogram PNG

    Returns:
        Acoustic analysis including spectral, temporal, and perceptual metrics
    """
    # Call CLI and parse JSON output
    result = await run_cli(["analyze", file_path, "--json", ...])
    return AnalysisResult(**json.loads(result))
```

### Pattern 2: CLI Subprocess Wrapper
**What:** Use asyncio subprocess to call audioloop CLI
**When to use:** All tool implementations
**Example:**
```python
# Source: Python asyncio docs + MCP patterns
import asyncio
import json
import sys

async def run_cli(args: list[str]) -> str:
    """Run audioloop CLI command and return stdout."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "audioloop", *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"audioloop failed: {stderr.decode()}")

    return stdout.decode()
```

### Pattern 3: Image Resource for Spectrograms
**What:** Return spectrogram PNG as Image content that Claude can view
**When to use:** When spectrogram is requested
**Example:**
```python
# Source: MCP Python SDK Image handling
from mcp.server.fastmcp import FastMCP, Image
from pathlib import Path

@mcp.tool()
async def analyze_with_spectrogram(file_path: str) -> tuple[AnalysisResult, Image]:
    """Analyze audio and return spectrogram image."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        spec_path = f.name

    # Run analysis with spectrogram generation
    result = await run_cli([
        "analyze", file_path, "--json",
        "--spectrogram", spec_path
    ])

    # Read spectrogram image
    image_data = Path(spec_path).read_bytes()
    Path(spec_path).unlink()  # cleanup

    return (
        AnalysisResult(**json.loads(result)),
        Image(data=image_data, format="png")
    )
```

### Pattern 4: Lifespan for Resource Management
**What:** Use FastMCP lifespan for setup/teardown
**When to use:** If server needs initialization (not required for audioloop)
**Example:**
```python
# Source: MCP Python SDK lifespan docs
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    # Startup: verify audioloop is installed
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "audioloop", "--version",
        stdout=asyncio.subprocess.PIPE
    )
    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("audioloop not installed")
    yield
    # Shutdown: nothing needed

mcp = FastMCP("audioloop", lifespan=app_lifespan)
```

### Anti-Patterns to Avoid
- **Printing to stdout:** All logs/debug must go to stderr. stdout is for MCP protocol only.
- **Sync subprocess in async tool:** Use `asyncio.create_subprocess_exec`, not `subprocess.run`
- **Giant tool with many params:** Split into separate tools (render, analyze, iterate, compare)
- **Returning raw CLI output:** Parse JSON and return structured Pydantic models
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON-RPC protocol | Custom message parsing | FastMCP/mcp SDK | Protocol is complex, version negotiation, lifecycle |
| Schema generation | Manual JSON schemas | Pydantic + type hints | Automatic, validated, keeps code DRY |
| Transport layer | Raw stdin/stdout handling | `mcp.run()` | Handles buffering, framing, errors |
| Tool registration | Custom routing | `@mcp.tool()` decorator | Automatic discovery, schema generation |
| Image encoding | Manual base64 | `Image()` class | Handles encoding, MIME types |
| Progress updates | Custom notifications | `ctx.report_progress()` | Protocol-compliant progress |

**Key insight:** The MCP SDK exists precisely because the protocol is non-trivial. FastMCP handles JSON-RPC 2.0 message framing, capability negotiation, tool/resource discovery, and transport abstraction. Rolling your own means reimplementing a protocol that took Anthropic months to design.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: stdout Pollution
**What goes wrong:** Server outputs debug info to stdout, breaking protocol
**Why it happens:** Python print() defaults to stdout
**How to avoid:**
- Use `sys.stderr.write()` or logging to stderr
- Set `logging.basicConfig(stream=sys.stderr)`
- Never use `print()` in MCP server code
**Warning signs:** Client reports "invalid JSON" or connection drops

### Pitfall 2: Working Directory Assumptions
**What goes wrong:** Server can't find files with relative paths
**Why it happens:** Claude Desktop/Code may launch server from root directory
**How to avoid:**
- Always accept and use absolute paths
- Resolve paths with `Path(path).resolve()` before use
- Don't assume cwd is the project directory
**Warning signs:** FileNotFoundError for files that exist

### Pitfall 3: Missing Environment Variables
**What goes wrong:** Server can't find dependencies (sclang, etc.)
**Why it happens:** MCP servers only inherit USER, HOME, PATH by default
**How to avoid:**
- Document required env vars
- Check for dependencies at startup (lifespan)
- Use absolute paths for executables
**Warning signs:** "command not found" errors

### Pitfall 4: Blocking Async with Sync Subprocess
**What goes wrong:** Server appears to hang during long renders
**Why it happens:** Using `subprocess.run()` blocks the event loop
**How to avoid:** Always use `asyncio.create_subprocess_exec()`
**Warning signs:** Client timeouts, unresponsive server

### Pitfall 5: Overly Complex Tool Schemas
**What goes wrong:** Claude gets confused by too many parameters
**Why it happens:** Trying to expose every CLI flag as a parameter
**How to avoid:**
- Provide sensible defaults
- Only expose parameters Claude needs to vary
- Use separate tools for different use cases
**Warning signs:** Claude misuses parameters, forgets required ones

### Pitfall 6: No Error Context
**What goes wrong:** Claude can't diagnose render failures
**Why it happens:** Returning generic "command failed" errors
**How to avoid:**
- Include stderr from subprocess in error messages
- Parse SuperCollider error output when possible
- Distinguish between "your code has errors" vs "system failed"
**Warning signs:** Claude keeps regenerating same broken code
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Complete FastMCP Server Skeleton
```python
# Source: MCP Python SDK docs
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "audioloop",
    json_response=True,  # Enable structured JSON output
)

@mcp.tool()
def render(
    file_path: str,
    duration: float | None = None,
    output: str | None = None
) -> dict:
    """Render SuperCollider code to WAV file.

    Args:
        file_path: Path to .scd file
        duration: Duration in seconds (for simple function mode)
        output: Output WAV path (defaults to same name as input)

    Returns:
        Render result with output file path and any warnings
    """
    ...

@mcp.tool()
def analyze(file_path: str, no_psychoacoustic: bool = False) -> dict:
    """Analyze audio file acoustically."""
    ...

@mcp.tool()
def iterate(
    file_path: str,
    duration: float | None = None,
    no_psychoacoustic: bool = False
) -> dict:
    """Render, analyze, and open for playback in one step."""
    ...

if __name__ == "__main__":
    mcp.run()  # Defaults to stdio transport
```

### Testing with In-Memory Transport
```python
# Source: MCP Python SDK testing docs
import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from audioloop.mcp_server import mcp

@pytest.fixture
async def client_session():
    async with create_connected_server_and_client_session(
        mcp, raise_exceptions=True
    ) as session:
        yield session

@pytest.mark.anyio
async def test_analyze_tool(client_session: ClientSession):
    result = await client_session.call_tool(
        "analyze",
        {"file_path": "/path/to/test.wav"}
    )
    assert result.structuredContent is not None
    assert "spectral" in result.structuredContent
```

### Running Server for Claude Code
```bash
# Add to Claude Code MCP configuration
claude mcp add audioloop -- python -m audioloop.mcp_server

# Or in .mcp.json
{
  "mcpServers": {
    "audioloop": {
      "command": "python",
      "args": ["-m", "audioloop.mcp_server"]
    }
  }
}
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SSE transport | Streamable HTTP or stdio | 2025-03 | SSE deprecated in spec |
| Manual JSON schemas | Pydantic auto-generation | 2024 | Much simpler, less error-prone |
| v1.x SDK | v2.x coming Q1 2026 | In progress | May have breaking changes |
| FastMCP 1.0 | FastMCP in official SDK | 2024 | Now part of mcp package |

**New tools/patterns to consider:**
- **Structured Output (2025-06):** `outputSchema` in tool definition enables validated structured responses
- **MCP Inspector:** Essential debugging tool, launch with `uv run mcp dev server.py`
- **Tasks (experimental):** Long-running operations with progress, may be useful for slow renders

**Deprecated/outdated:**
- **SSE transport:** Deprecated as of spec 2025-03-26, use stdio or streamable-http
- **Separate fastmcp package:** Now integrated into official mcp package
- **Python 3.9:** Minimum is now Python 3.10
</sota_updates>

<open_questions>
## Open Questions

1. **Tool granularity**
   - What we know: Could have single `audioloop` tool with subcommand param, or separate tools
   - What's unclear: What granularity works best for Claude's tool selection
   - Recommendation: Start with separate tools (render, analyze, iterate, compare, play) - clearer schemas

2. **Spectrogram return method**
   - What we know: Can return as Image content or as resource
   - What's unclear: Whether Claude handles inline images better than resources
   - Recommendation: Return as `Image` in tool result for simplicity; test in practice

3. **Human vs JSON output**
   - What we know: CLI has both formats
   - What's unclear: Whether to include human-readable alongside JSON
   - Recommendation: Return only JSON/structured data - Claude interprets better

4. **Error handling for SC syntax errors**
   - What we know: CLI returns SC error messages in JSON
   - What's unclear: Best format for Claude to parse and fix
   - Recommendation: Include full stderr in error response, let Claude parse
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- /modelcontextprotocol/python-sdk - FastMCP, tools, resources, testing, Image handling
- https://pypi.org/project/mcp/ - Version 1.25.0, installation
- https://modelcontextprotocol.io/legacy/tools/debugging - Debugging guide, common issues

### Secondary (MEDIUM confidence)
- https://github.com/modelcontextprotocol/python-sdk - Repository structure, examples
- https://mcpcat.io/guides/building-mcp-server-python-fastmcp/ - Tutorial verified against SDK
- https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers - Error patterns

### Tertiary (LOW confidence - needs validation)
- Tool granularity recommendations - based on patterns observed, not official guidance
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: MCP Python SDK (FastMCP)
- Ecosystem: Pydantic, asyncio, pytest
- Patterns: Tool decorators, subprocess wrappers, structured output
- Pitfalls: stdout pollution, paths, env vars, blocking

**Confidence breakdown:**
- Standard stack: HIGH - official SDK, verified versions
- Architecture: HIGH - patterns from SDK docs and Context7
- Pitfalls: HIGH - documented in official debugging guide
- Code examples: HIGH - from Context7/official sources

**Research date:** 2026-01-11
**Valid until:** 2026-02-11 (30 days - SDK stable but v2 coming)
</metadata>

---

*Phase: 08-mcp-server*
*Research completed: 2026-01-11*
*Ready for planning: yes*
