"""Shared layout utilities for CLI output formatting.

Centralizes styling so all commands have consistent appearance.
"""

from rich.console import Console

# Layout constants
INDENT = "  "
LABEL_WIDTH = 14
VALUE_WIDTH = 20  # For L/R columns in spectral


def section(console: Console, title: str) -> None:
    """Print a section header with ─── TITLE ──────── format.

    Args:
        console: Rich Console to print to.
        title: Section title text.
    """
    dashes = "─" * (50 - len(title))
    console.print(f"{INDENT}─── {title} {dashes}")


def row(console: Console, label: str, value: str) -> None:
    """Print a key-value row.

    Args:
        console: Rich Console to print to.
        label: Row label.
        value: Row value.
    """
    console.print(f"{INDENT}{label:<{LABEL_WIDTH}} {value}")


def row3(console: Console, label: str, left: str, right: str) -> None:
    """Print a three-column row (for L/R spectral data).

    Args:
        console: Rich Console to print to.
        label: Row label.
        left: Left channel value.
        right: Right channel value.
    """
    console.print(f"{INDENT}{label:<{LABEL_WIDTH}} {left:<{VALUE_WIDTH}} {right}")
