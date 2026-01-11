"""Interpretation layer for analysis results.

Provides human-readable context for raw acoustic measurements.
These are reference ranges, not judgments - interpretation depends on context.
"""

from io import StringIO

from rich.console import Console

from audioloop.analyze import AnalysisResult
from audioloop.layout import section, row, row3, num, path


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

    return f"{num(f'{hz:.0f}')} Hz ({desc})"


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

    return f"{num(f'{cf:.1f}')} ({desc})"


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

    return f"{num(f'{width:.2f}')} ({desc})"


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

    return f"{num(f'{lufs:.1f}')} LUFS ({desc})"


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
    return f"{num(f'{sones:.1f}')} sone ({desc})"


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
    return f"{num(f'{acum:.2f}')} acum ({desc})"


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
    return f"{num(f'{asper:.3f}')} asper ({desc})"


def format_band_bar(energy: float, width: int = 10) -> str:
    """Format an ASCII bar representing energy level.

    Args:
        energy: Normalized energy value (0-1).
        width: Total width of the bar in characters.

    Returns:
        ASCII bar string like "███░░░░░░░"
    """
    filled = int(round(energy * width))
    empty = width - filled
    return "█" * filled + "░" * empty


def print_analysis_human(result: AnalysisResult, console: Console) -> None:
    """Print analysis result as human-readable output directly to console.

    Uses rich Tables for aligned output with proper terminal formatting.

    Args:
        result: AnalysisResult from analyze().
        console: Rich Console to print to.
    """
    _render_analysis_tables(result, console)


def format_analysis_human(result: AnalysisResult) -> str:
    """Format analysis result as human-readable output string.

    Uses rich Tables for aligned output. Returns plain text without ANSI codes.

    Args:
        result: AnalysisResult from analyze().

    Returns:
        Formatted string with all analysis sections.
    """
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=False)
    _render_analysis_tables(result, console)
    return string_io.getvalue()


def _render_analysis_tables(result: AnalysisResult, console: Console) -> None:
    """Render analysis tables to the given console.

    Args:
        result: AnalysisResult from analyze().
        console: Rich Console to render to.
    """
    # FILE INFO section
    section(console, "FILE INFO")
    row(console, "File", path(result.file))
    row(console, "Duration", f"{num(f'{result.duration_sec:.2f}')}s")
    row(console, "Sample Rate", f"{num(str(result.sample_rate))} Hz")
    row(console, "Channels", num(str(result.channels)))
    console.print()

    # SPECTRAL section - L/R columns
    section(console, "SPECTRAL")
    left = result.spectral["left"]
    right = result.spectral["right"]

    row3(console, "", "Left", "Right")
    row3(console, "Centroid", interpret_centroid(left["centroid_hz"]), interpret_centroid(right["centroid_hz"]))
    row3(console, "Rolloff (85%)", f"{num(f'{left['rolloff_hz']:.0f}')} Hz", f"{num(f'{right['rolloff_hz']:.0f}')} Hz")
    row3(console, "Flatness", num(f"{left['flatness']:.3f}"), num(f"{right['flatness']:.3f}"))
    row3(console, "Bandwidth", f"{num(f'{left['bandwidth_hz']:.0f}')} Hz", f"{num(f'{right['bandwidth_hz']:.0f}')} Hz")
    console.print()

    # DYNAMICS section
    section(console, "DYNAMICS")
    row(console, "RMS", num(f"{result.temporal['rms']:.4f}"))
    row(console, "Crest Factor", interpret_crest_factor(result.temporal["crest_factor"]))
    row(console, "Attack", f"{num(f'{result.temporal['attack_ms']:.1f}')} ms")
    console.print()

    # STEREO section
    section(console, "STEREO")
    row(console, "Width", interpret_stereo_width(result.stereo["width"]))
    row(console, "Correlation", num(f"{result.stereo['correlation']:.2f}"))
    console.print()

    # LOUDNESS section
    section(console, "LOUDNESS")
    row(console, "Integrated", interpret_loudness(result.loudness_lufs))

    # PSYCHOACOUSTIC section (if data available)
    if result.psychoacoustic:
        console.print()
        section(console, "PSYCHOACOUSTIC")
        if "loudness_sone" in result.psychoacoustic:
            row(console, "Zwicker", interpret_zwicker_loudness(result.psychoacoustic["loudness_sone"]))
        if "sharpness_acum" in result.psychoacoustic:
            row(console, "Sharpness", interpret_sharpness(result.psychoacoustic["sharpness_acum"]))
        if "roughness_asper" in result.psychoacoustic:
            row(console, "Roughness", interpret_roughness(result.psychoacoustic["roughness_asper"]))

    # FREQUENCY BANDS section (if data available)
    if result.band_energies:
        console.print()
        section(console, "FREQUENCY BANDS")
        # Display bands in order with labels
        band_labels = {
            "sub": "Sub (20-60)",
            "bass": "Bass (60-250)",
            "low_mid": "Low-mid",
            "mid": "Mid (500-2k)",
            "high_mid": "High-mid",
            "high": "High (4k-20k)",
        }
        for band_key in ["sub", "bass", "low_mid", "mid", "high_mid", "high"]:
            if band_key in result.band_energies:
                energy = result.band_energies[band_key]
                bar = format_band_bar(energy)
                label = band_labels.get(band_key, band_key)
                row(console, label, f"{bar}  {num(f'{energy:.2f}')}")
