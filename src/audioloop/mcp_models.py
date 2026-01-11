"""Pydantic models for MCP server tool schemas.

These models match the exact JSON output structure from the CLI commands.
They enable automatic JSON schema generation for MCP tool definitions.
"""

from pydantic import BaseModel, Field


class RenderError(BaseModel):
    """SuperCollider render error details."""

    message: str = Field(description="Error message from SuperCollider")
    file: str | None = Field(default=None, description="File where error occurred")
    line: int | None = Field(default=None, description="Line number of error")
    char: int | None = Field(default=None, description="Character position of error")


class RenderResult(BaseModel):
    """Result from render command."""

    success: bool = Field(description="Whether render succeeded")
    output_path: str | None = Field(default=None, description="Path to rendered WAV file")
    duration_sec: float | None = Field(default=None, description="Duration of rendered audio in seconds")
    render_time_sec: float = Field(description="Time taken to render in seconds")
    mode: str | None = Field(default=None, description="Render mode used: 'nrt' or 'simple'")
    error: RenderError | None = Field(default=None, description="Error details if render failed")


class SpectralFeatures(BaseModel):
    """Spectral features for a single channel."""

    centroid_hz: float = Field(description="Spectral centroid in Hz - brightness indicator")
    rolloff_hz: float = Field(description="Frequency below which 85% of energy lies")
    flatness: float = Field(description="Spectral flatness (0-1), higher = more noise-like")
    bandwidth_hz: float = Field(description="Spectral bandwidth in Hz")


class ChannelSpectral(BaseModel):
    """Spectral features for left and right channels."""

    left: SpectralFeatures = Field(description="Left channel spectral features")
    right: SpectralFeatures = Field(description="Right channel spectral features")


class TemporalFeatures(BaseModel):
    """Temporal/dynamics features."""

    attack_ms: float = Field(description="Attack time in milliseconds")
    rms: float = Field(description="Root mean square energy level")
    crest_factor: float = Field(description="Peak to RMS ratio - dynamic range indicator")


class StereoFeatures(BaseModel):
    """Stereo imaging features."""

    width: float = Field(description="Stereo width (0-1), higher = wider stereo image")
    correlation: float = Field(description="L-R correlation (-1 to +1), +1 = identical channels")


class PsychoacousticFeatures(BaseModel):
    """Psychoacoustic metrics from Zwicker model."""

    sharpness_acum: float | None = Field(default=None, description="Sharpness in acum (perceptual brightness)")
    roughness_asper: float | None = Field(default=None, description="Roughness in asper (modulation roughness)")
    loudness_sone: float | None = Field(default=None, description="Loudness in sone (perceived loudness)")
    loudness_sone_max: float | None = Field(default=None, description="Maximum loudness in sone")


class BandEnergies(BaseModel):
    """Frequency band energy distribution (normalized 0-1)."""

    sub: float = Field(description="Sub bass energy (20-60 Hz)")
    bass: float = Field(description="Bass energy (60-250 Hz)")
    low_mid: float = Field(description="Low mid energy (250-500 Hz)")
    mid: float = Field(description="Mid energy (500-2000 Hz)")
    high_mid: float = Field(description="High mid energy (2000-4000 Hz)")
    high: float = Field(description="High frequency energy (4000-20000 Hz)")


class AnalysisResult(BaseModel):
    """Complete analysis result for an audio file."""

    file: str = Field(description="Path to analyzed file")
    duration_sec: float = Field(description="Duration in seconds")
    sample_rate: int = Field(description="Sample rate in Hz")
    channels: int = Field(description="Number of audio channels")
    spectral: ChannelSpectral = Field(description="Per-channel spectral features")
    temporal: TemporalFeatures = Field(description="Temporal dynamics features")
    stereo: StereoFeatures = Field(description="Stereo imaging features")
    loudness_lufs: float = Field(description="Integrated loudness in LUFS")
    psychoacoustic: PsychoacousticFeatures | None = Field(
        default=None, description="Psychoacoustic metrics (may be empty if skipped)"
    )
    band_energies: BandEnergies = Field(description="Frequency band energy distribution")
    spectrogram_path: str | None = Field(default=None, description="Path to spectrogram PNG if generated")


class IterateRender(BaseModel):
    """Render portion of iterate result."""

    success: bool = Field(description="Whether render succeeded")
    output_path: str | None = Field(default=None, description="Path to rendered WAV file")
    duration_sec: float | None = Field(default=None, description="Duration of rendered audio")
    render_time_sec: float = Field(description="Time taken to render")
    mode: str | None = Field(default=None, description="Render mode: 'nrt' or 'simple'")
    error: RenderError | None = Field(default=None, description="Error details if render failed")


class IterateResult(BaseModel):
    """Result from iterate command (render + analyze + play)."""

    success: bool = Field(description="Whether full iterate pipeline succeeded")
    render: IterateRender | None = Field(default=None, description="Render step result")
    analysis: AnalysisResult | None = Field(default=None, description="Analysis result if render succeeded")
    played: bool = Field(description="Whether audio was played")
    output_path: str | None = Field(default=None, description="Path to WAV file if kept")
    total_time_sec: float = Field(description="Total time for iterate pipeline")
    play_error: str | None = Field(default=None, description="Playback error message if play failed")
    spectrogram_path: str | None = Field(default=None, description="Path to spectrogram PNG if generated")
    error: str | None = Field(default=None, description="Top-level error message")


class FeatureDelta(BaseModel):
    """Delta between two feature values."""

    metric: str = Field(description="Full metric path (e.g., 'spectral.left.centroid_hz')")
    value_a: float = Field(description="Value from baseline file")
    value_b: float = Field(description="Value from comparison file")
    delta: float = Field(description="Absolute change (value_b - value_a)")
    percent_change: float | None = Field(default=None, description="Percentage change from baseline")
    direction: str = Field(description="Change direction: 'up', 'down', or 'unchanged'")
    significant: bool = Field(description="Whether change exceeds 10% threshold")
    unit: str = Field(description="Unit of measurement (Hz, ms, LUFS, etc.)")
    interpretation: str | None = Field(default=None, description="Human-readable interpretation of change")


class ComparisonSummary(BaseModel):
    """Summary statistics for comparison."""

    significant_changes: list[str] = Field(description="List of metrics with significant changes")
    total_metrics: int = Field(description="Total number of metrics compared")
    changed_count: int = Field(description="Number of metrics that changed")
    significant_count: int = Field(description="Number of significant changes (>10%)")
    interpretations: list[str] | None = Field(default=None, description="Human-readable change descriptions")


class ComparisonResult(BaseModel):
    """Result from compare command."""

    file_a: str = Field(description="Path to baseline file")
    file_b: str = Field(description="Path to comparison file")
    duration_a: float = Field(description="Duration of baseline file")
    duration_b: float = Field(description="Duration of comparison file")
    summary: ComparisonSummary = Field(description="Summary of comparison")
    deltas: dict[str, FeatureDelta] = Field(description="Per-metric deltas keyed by metric path")
