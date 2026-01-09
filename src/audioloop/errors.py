"""SuperCollider error detection and parsing."""

import re
from dataclasses import dataclass


@dataclass
class SCError:
    """Structured SuperCollider error information."""

    message: str
    file: str | None = None
    line: int | None = None
    char: int | None = None


# Patterns that indicate an error occurred in sclang output
ERROR_PATTERNS = [
    r"\bERROR\b",
    r"Library has not been compiled successfully",
    r"FAILURE IN SERVER",
]


def has_error(output: str) -> bool:
    """Check if sclang output contains errors.

    Args:
        output: The stdout from sclang execution.

    Returns:
        True if any error pattern is found.
    """
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, output, re.IGNORECASE):
            return True
    return False


def extract_error(output: str) -> SCError | None:
    """Extract structured error information from sclang output.

    Parses error format like:
        ERROR: syntax error, unexpected BINOP
          in file '/path/to/file.scd'
          line 12 char 5

    Args:
        output: The stdout from sclang execution.

    Returns:
        SCError with parsed details, or None if no error found.
    """
    # Try to match the full structured error format
    structured_pattern = (
        r"ERROR:\s*(.+?)\n"
        r"\s+in file '([^']+)'\n"
        r"\s+line (\d+) char (\d+)"
    )
    match = re.search(structured_pattern, output)
    if match:
        return SCError(
            message=match.group(1).strip(),
            file=match.group(2),
            line=int(match.group(3)),
            char=int(match.group(4)),
        )

    # Try to match ERROR: message without file/line info
    simple_pattern = r"ERROR:\s*(.+?)(?:\n|$)"
    match = re.search(simple_pattern, output)
    if match:
        return SCError(message=match.group(1).strip())

    # Check for library compilation failure
    if "Library has not been compiled successfully" in output:
        return SCError(message="Library compilation failed")

    # Check for server failure
    if "FAILURE IN SERVER" in output:
        failure_pattern = r"FAILURE IN SERVER\s+(.+?)(?:\n|$)"
        match = re.search(failure_pattern, output)
        message = match.group(1).strip() if match else "Server failure"
        return SCError(message=message)

    return None


def format_error_human(error: SCError) -> str:
    """Format an SCError for human-readable display.

    Args:
        error: The error to format.

    Returns:
        A formatted string suitable for terminal output.
    """
    parts = [f"Error: {error.message}"]

    if error.file:
        parts.append(f"  File: {error.file}")

    if error.line is not None:
        location = f"  Line {error.line}"
        if error.char is not None:
            location += f", Column {error.char}"
        parts.append(location)

    return "\n".join(parts)
