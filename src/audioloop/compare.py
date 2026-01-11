"""Audio comparison module for feature delta analysis.

Compares two audio files and computes interpretable deltas
for Claude and human feedback loops.
"""

from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Literal

from rich.console import Console

from audioloop.analyze import analyze, AnalysisError
from audioloop.layout import INDENT, section


# Direction and significance interpretations for common metrics
INTERPRETATIONS = {
    "centroid_hz": {
        "down": "darker/warmer",
        "up": "brighter",
    },
    "rolloff_hz": {
        "down": "less high frequency content",
        "up": "more high frequency content",
    },
    "bandwidth_hz": {
        "down": "narrower spectrum",
        "up": "wider spectrum",
    },
    "attack_ms": {
        "down": "snappier attack",
        "up": "slower attack",
    },
    "rms": {
        "down": "quieter",
        "up": "louder",
    },
    "crest_factor": {
        "down": "more compressed",
        "up": "more dynamic",
    },
    "width": {
        "down": "narrower stereo",
        "up": "wider stereo",
    },
    "correlation": {
        "down": "less correlated L/R",
        "up": "more correlated L/R",
    },
    "loudness_lufs": {
        "down": "quieter",
        "up": "louder",
    },
    # Psychoacoustic interpretations
    "loudness_sone": {
        "down": "quieter (perceived)",
        "up": "louder (perceived)",
    },
    "loudness_sone_max": {
        "down": "lower peak loudness",
        "up": "higher peak loudness",
    },
    "sharpness_acum": {
        "down": "duller/softer",
        "up": "sharper/brighter",
    },
    "roughness_asper": {
        "down": "smoother",
        "up": "rougher/grittier",
    },
}


# Units for each metric
UNITS = {
    "centroid_hz": "Hz",
    "rolloff_hz": "Hz",
    "bandwidth_hz": "Hz",
    "flatness": "",
    "attack_ms": "ms",
    "rms": "",
    "crest_factor": "",
    "width": "",
    "correlation": "",
    "loudness_lufs": "LUFS",
    "duration_sec": "s",
    # Psychoacoustic units
    "loudness_sone": "sone",
    "loudness_sone_max": "sone",
    "sharpness_acum": "acum",
    "roughness_asper": "asper",
}


@dataclass
class FeatureDelta:
    """Delta between two feature values."""

    metric: str
    value_a: float
    value_b: float
    delta: float
    percent_change: float | None  # None if division by zero
    direction: Literal["up", "down", "unchanged"]
    significant: bool  # abs(percent_change) > 10
    unit: str
    interpretation: str | None = None


@dataclass
class ComparisonResult:
    """Complete comparison result between two audio files."""

    file_a: str
    file_b: str
    duration_a: float
    duration_b: float
    deltas: dict[str, FeatureDelta] = field(default_factory=dict)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_a": self.file_a,
            "file_b": self.file_b,
            "duration_a": self.duration_a,
            "duration_b": self.duration_b,
            "summary": self.summary,
            "deltas": {
                key: {
                    "metric": d.metric,
                    "value_a": d.value_a,
                    "value_b": d.value_b,
                    "delta": d.delta,
                    "percent_change": d.percent_change,
                    "direction": d.direction,
                    "significant": d.significant,
                    "unit": d.unit,
                    "interpretation": d.interpretation,
                }
                for key, d in self.deltas.items()
            },
        }


def _flatten_analysis(analysis_dict: dict, prefix: str = "") -> dict[str, float]:
    """Flatten nested analysis dict to dot-separated keys.

    E.g., {"spectral": {"left": {"centroid_hz": 440}}}
    becomes {"spectral.left.centroid_hz": 440}
    """
    result = {}
    for key, value in analysis_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_analysis(value, full_key))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            result[full_key] = float(value)
    return result


def _get_metric_name(full_key: str) -> str:
    """Extract the base metric name from a flattened key.

    E.g., "spectral.left.centroid_hz" -> "centroid_hz"
    """
    return full_key.split(".")[-1]


def _get_unit(full_key: str) -> str:
    """Get unit for a metric from its full key."""
    metric_name = _get_metric_name(full_key)
    return UNITS.get(metric_name, "")


def _get_interpretation(full_key: str, direction: str) -> str | None:
    """Get interpretation text for a metric and direction."""
    metric_name = _get_metric_name(full_key)
    if metric_name in INTERPRETATIONS:
        return INTERPRETATIONS[metric_name].get(direction)
    return None


def compare_audio(file_a: Path, file_b: Path) -> ComparisonResult:
    """Compare two audio files and compute feature deltas.

    Args:
        file_a: First audio file (baseline).
        file_b: Second audio file (comparison).

    Returns:
        ComparisonResult with all computed deltas.

    Raises:
        AnalysisError: If either file cannot be analyzed.
    """
    file_a = Path(file_a)
    file_b = Path(file_b)

    # Analyze both files
    analysis_a = analyze(file_a)
    analysis_b = analyze(file_b)

    # Flatten to comparable format
    flat_a = _flatten_analysis(analysis_a.to_dict())
    flat_b = _flatten_analysis(analysis_b.to_dict())

    # Compute deltas for all shared numeric fields
    deltas: dict[str, FeatureDelta] = {}
    significant_changes: list[str] = []

    # Skip metadata fields
    skip_keys = {"file", "sample_rate", "channels"}

    for key in flat_a:
        if key in skip_keys:
            continue
        if key not in flat_b:
            continue

        val_a = flat_a[key]
        val_b = flat_b[key]
        delta = val_b - val_a

        # Percent change (handle zero base value)
        if abs(val_a) > 1e-10:
            pct = (delta / abs(val_a)) * 100
        else:
            pct = None

        # Direction
        if abs(delta) < 1e-10:
            direction = "unchanged"
        else:
            direction = "up" if delta > 0 else "down"

        # Significance (>10% change)
        significant = pct is not None and abs(pct) > 10

        # Get interpretation for significant changes
        interpretation = None
        if significant and direction != "unchanged":
            interpretation = _get_interpretation(key, direction)
            significant_changes.append(key)

        deltas[key] = FeatureDelta(
            metric=key,
            value_a=val_a,
            value_b=val_b,
            delta=delta,
            percent_change=pct,
            direction=direction,
            significant=significant,
            unit=_get_unit(key),
            interpretation=interpretation,
        )

    # Build summary
    summary = {
        "significant_changes": significant_changes,
        "total_metrics": len(deltas),
        "changed_count": sum(1 for d in deltas.values() if d.direction != "unchanged"),
        "significant_count": sum(1 for d in deltas.values() if d.significant),
    }

    # Add overall interpretation
    interpretations = [
        d.interpretation for d in deltas.values() if d.interpretation is not None
    ]
    if interpretations:
        summary["interpretations"] = interpretations

    return ComparisonResult(
        file_a=str(file_a),
        file_b=str(file_b),
        duration_a=analysis_a.duration_sec,
        duration_b=analysis_b.duration_sec,
        deltas=deltas,
        summary=summary,
    )


def print_comparison_human(result: ComparisonResult, console: Console) -> None:
    """Print comparison result as human-readable output.

    Args:
        result: ComparisonResult from compare_audio().
        console: Rich Console to print to.
    """
    # Header
    console.print(f"[bold]Comparison:[/bold] {result.file_a} -> {result.file_b}")
    console.print(
        f"Duration: {result.duration_a:.2f}s -> {result.duration_b:.2f}s"
    )
    console.print()

    # Group deltas by category
    categories = {
        "spectral": [],
        "temporal": [],
        "stereo": [],
        "loudness": [],
        "psychoacoustic": [],
    }

    for key, delta in result.deltas.items():
        if key.startswith("spectral"):
            categories["spectral"].append((key, delta))
        elif key.startswith("temporal"):
            categories["temporal"].append((key, delta))
        elif key.startswith("stereo"):
            categories["stereo"].append((key, delta))
        elif key.startswith("psychoacoustic"):
            categories["psychoacoustic"].append((key, delta))
        elif "loudness" in key or "lufs" in key.lower():
            categories["loudness"].append((key, delta))

    # Display each category
    for cat_name, cat_deltas in categories.items():
        if not cat_deltas:
            continue

        # Check if any significant changes
        has_significant = any(d.significant for _, d in cat_deltas)

        title = cat_name.upper()
        if has_significant:
            title += " (changes)"

        section(console, title)

        for key, delta in cat_deltas:
            # Skip duration_sec from any category
            if "duration_sec" in key:
                continue

            # Format values
            metric_name = _get_metric_name(key)

            # Add channel label for per-channel metrics
            if ".left." in key:
                metric_name += " (L)"
            elif ".right." in key:
                metric_name += " (R)"
            unit = delta.unit

            # Value formatting based on magnitude
            if abs(delta.value_a) > 100:
                val_a_str = f"{delta.value_a:.0f}"
                val_b_str = f"{delta.value_b:.0f}"
                delta_str = f"{delta.delta:+.0f}"
            elif abs(delta.value_a) > 1:
                val_a_str = f"{delta.value_a:.2f}"
                val_b_str = f"{delta.value_b:.2f}"
                delta_str = f"{delta.delta:+.2f}"
            else:
                val_a_str = f"{delta.value_a:.4f}"
                val_b_str = f"{delta.value_b:.4f}"
                delta_str = f"{delta.delta:+.4f}"

            if unit:
                val_a_str += f" {unit}"
                val_b_str += f" {unit}"
                delta_str += f" {unit}"

            # Direction arrow
            if delta.direction == "up":
                arrow = "[green]↑[/green]"
            elif delta.direction == "down":
                arrow = "[red]↓[/red]"
            else:
                arrow = "[dim]=[/dim]"

            # Percent change
            pct_str = ""
            if delta.percent_change is not None and abs(delta.percent_change) < 10000:
                pct_str = f" ({delta.percent_change:+.1f}%)"

            console.print(f"{INDENT}{metric_name:<18} {val_a_str:<12} → {val_b_str:<12} {arrow} {delta_str}{pct_str}")

        console.print()

    # Summary
    if result.summary.get("interpretations"):
        console.print("[bold]Summary:[/bold]", ", ".join(result.summary["interpretations"]))


def format_comparison_human(result: ComparisonResult) -> str:
    """Format comparison result as human-readable output (for testing).

    Args:
        result: ComparisonResult from compare_audio().

    Returns:
        Plain text string with comparison (no ANSI codes).
    """
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=False, no_color=True)
    print_comparison_human(result, console)
    return string_io.getvalue()
