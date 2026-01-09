"""Interpretation layer for analysis results.

Provides human-readable context for raw acoustic measurements.
These are reference ranges, not judgments - interpretation depends on context.
"""

from io import StringIO

from rich.console import Console
from rich.table import Table

from audioloop.analyze import AnalysisResult


def interpret_centroid(hz: float) -> str:
    """Add reference context to spectral centroid value.

    Args:
        hz: Spectral centroid in Hz.

    Returns:
        Formatted string with value and reference range.
    """
    if hz < 300:
        desc = "very dark"
    elif hz < 800:
        desc = "dark/warm"
    elif hz < 2000:
        desc = "neutral"
    elif hz < 4000:
        desc = "bright"
    else:
        desc = "very bright"

    return f"{hz:.0f} Hz ({desc})"


def interpret_crest_factor(cf: float) -> str:
    """Add reference context to crest factor value.

    Args:
        cf: Crest factor (peak / RMS ratio).

    Returns:
        Formatted string with value and dynamics context.
    """
    if cf < 3:
        desc = "very compressed"
    elif cf < 10:
        desc = "moderate dynamics"
    elif cf < 20:
        desc = "punchy/dynamic"
    else:
        desc = "very dynamic"

    return f"{cf:.1f} ({desc})"


def interpret_stereo_width(width: float) -> str:
    """Add reference context to stereo width value.

    Args:
        width: Stereo width (0-1, side energy ratio).

    Returns:
        Formatted string with value and width context.
    """
    if width < 0.1:
        desc = "mono"
    elif width < 0.3:
        desc = "narrow"
    elif width < 0.6:
        desc = "moderate"
    elif width < 0.8:
        desc = "wide"
    else:
        desc = "very wide"

    return f"{width:.2f} ({desc})"


def interpret_loudness(lufs: float) -> str:
    """Add reference context to loudness value.

    Args:
        lufs: Integrated loudness in dB LUFS.

    Returns:
        Formatted string with value and reference context.
    """
    # Reference targets
    if lufs > -10:
        desc = "very loud, likely clipping"
    elif lufs > -14:
        desc = "loud, streaming target"
    elif lufs > -18:
        desc = "moderate"
    elif lufs > -24:
        desc = "quiet, broadcast range"
    else:
        desc = "very quiet"

    return f"{lufs:.1f} LUFS ({desc})"


def interpret_zwicker_loudness(sones: float) -> str:
    """Add reference context to Zwicker loudness value.

    Note: Sones are relative (uncalibrated). Values indicate
    perceived loudness relative to reference, not absolute SPL.

    Args:
        sones: Zwicker loudness in sones.

    Returns:
        Formatted string with value and perceptual context.
    """
    if sones < 5:
        desc = "quiet"
    elif sones < 20:
        desc = "moderate"
    elif sones < 50:
        desc = "loud"
    else:
        desc = "very loud"
    return f"{sones:.1f} sone ({desc})"


def interpret_sharpness(acum: float) -> str:
    """Add reference context to sharpness value.

    Acum scale: 1.0 = reference narrow-band noise at 1kHz.
    Higher = more high-frequency energy perceived.

    Args:
        acum: Sharpness in acum.

    Returns:
        Formatted string with value and perceptual context.
    """
    if acum < 1.0:
        desc = "dull/warm"
    elif acum < 2.0:
        desc = "neutral"
    elif acum < 3.0:
        desc = "bright"
    else:
        desc = "harsh/piercing"
    return f"{acum:.2f} acum ({desc})"


def interpret_roughness(asper: float) -> str:
    """Add reference context to roughness value.

    Asper scale: Perception of rapid amplitude modulation (20-300 Hz).
    0 = smooth, higher = more textured/gritty.

    Args:
        asper: Roughness in asper.

    Returns:
        Formatted string with value and perceptual context.
    """
    if asper < 0.1:
        desc = "smooth"
    elif asper < 0.5:
        desc = "slight texture"
    elif asper < 1.0:
        desc = "noticeable modulation"
    else:
        desc = "rough/gritty"
    return f"{asper:.3f} asper ({desc})"


def format_analysis_human(result: AnalysisResult) -> str:
    """Format analysis result as human-readable output.

    Uses rich Tables for aligned output. Keeps it concise for both
    human and Claude consumption.

    Args:
        result: AnalysisResult from analyze().

    Returns:
        Rich-formatted string with all analysis sections.
    """
    # Use StringIO to capture output without printing to stdout
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True)

    # FILE INFO section
    info_table = Table(title="FILE INFO", show_header=False, box=None)
    info_table.add_column("Key", style="dim")
    info_table.add_column("Value")

    info_table.add_row("File", result.file)
    info_table.add_row("Duration", f"{result.duration_sec:.2f}s")
    info_table.add_row("Sample Rate", f"{result.sample_rate} Hz")
    info_table.add_row("Channels", str(result.channels))

    console.print(info_table)
    console.print()

    # SPECTRAL section - L/R columns
    spectral_table = Table(title="SPECTRAL")
    spectral_table.add_column("Feature", style="dim")
    spectral_table.add_column("Left")
    spectral_table.add_column("Right")

    left = result.spectral["left"]
    right = result.spectral["right"]

    spectral_table.add_row(
        "Centroid",
        interpret_centroid(left["centroid_hz"]),
        interpret_centroid(right["centroid_hz"]),
    )
    spectral_table.add_row(
        "Rolloff (85%)",
        f"{left['rolloff_hz']:.0f} Hz",
        f"{right['rolloff_hz']:.0f} Hz",
    )
    spectral_table.add_row(
        "Flatness",
        f"{left['flatness']:.3f}",
        f"{right['flatness']:.3f}",
    )
    spectral_table.add_row(
        "Bandwidth",
        f"{left['bandwidth_hz']:.0f} Hz",
        f"{right['bandwidth_hz']:.0f} Hz",
    )

    console.print(spectral_table)
    console.print()

    # DYNAMICS section
    dynamics_table = Table(title="DYNAMICS", show_header=False, box=None)
    dynamics_table.add_column("Feature", style="dim")
    dynamics_table.add_column("Value")

    dynamics_table.add_row("RMS", f"{result.temporal['rms']:.4f}")
    dynamics_table.add_row(
        "Crest Factor", interpret_crest_factor(result.temporal["crest_factor"])
    )
    dynamics_table.add_row("Attack", f"{result.temporal['attack_ms']:.1f} ms")

    console.print(dynamics_table)
    console.print()

    # STEREO section
    stereo_table = Table(title="STEREO", show_header=False, box=None)
    stereo_table.add_column("Feature", style="dim")
    stereo_table.add_column("Value")

    stereo_table.add_row("Width", interpret_stereo_width(result.stereo["width"]))
    stereo_table.add_row("Correlation", f"{result.stereo['correlation']:.2f}")

    console.print(stereo_table)
    console.print()

    # LOUDNESS section
    loudness_table = Table(title="LOUDNESS", show_header=False, box=None)
    loudness_table.add_column("Feature", style="dim")
    loudness_table.add_column("Value")

    loudness_table.add_row("Integrated", interpret_loudness(result.loudness_lufs))

    console.print(loudness_table)

    # PSYCHOACOUSTIC section (if data available)
    if result.psychoacoustic:
        console.print()
        psych_table = Table(title="PSYCHOACOUSTIC", show_header=False, box=None)
        psych_table.add_column("Feature", style="dim")
        psych_table.add_column("Value")

        if "loudness_sone" in result.psychoacoustic:
            psych_table.add_row(
                "Zwicker Loudness",
                interpret_zwicker_loudness(result.psychoacoustic["loudness_sone"]),
            )
        if "sharpness_acum" in result.psychoacoustic:
            psych_table.add_row(
                "Sharpness",
                interpret_sharpness(result.psychoacoustic["sharpness_acum"]),
            )
        if "roughness_asper" in result.psychoacoustic:
            psych_table.add_row(
                "Roughness",
                interpret_roughness(result.psychoacoustic["roughness_asper"]),
            )

        console.print(psych_table)

    return string_io.getvalue()
