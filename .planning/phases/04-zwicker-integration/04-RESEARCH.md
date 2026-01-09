# Phase 4: Zwicker Model Integration - Research

**Researched:** 2026-01-09
**Domain:** Psychoacoustic metrics (Zwicker loudness, roughness, sharpness) via MoSQITo
**Confidence:** HIGH

<research_summary>
## Summary

Phase 4 adds psychoacoustic metrics to the existing analysis pipeline. Research confirms MoSQITo (v1.2.1) as the primary library for Zwicker-based metrics, with pyloudnorm (already integrated) providing LUFS loudness.

Key findings:
- **MoSQITo requires 48kHz mono audio** - preprocessing step needed for all inputs
- **Fluctuation strength is NOT implemented** - only loudness, sharpness, roughness available
- **MoSQITo is slow** - can take 50+ seconds for 30s audio even when parallelized
- **pyloudnorm already provides LUFS** - no new dependency needed for broadcast loudness

The integration requires:
1. Audio preprocessing (resample to 48kHz, convert to mono)
2. MoSQITo metric computation (loudness, sharpness, roughness)
3. Output integration into existing `analyze` JSON structure
4. Graceful degradation if MoSQITo unavailable (optional dependency)

**Primary recommendation:** Use MoSQITo directly (not Soundscapy wrapper) for simpler dependency chain. Add as optional dependency with graceful fallback. Preprocess audio inline rather than creating temp files.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for psychoacoustic analysis:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| MoSQITo | 1.2.1 | Zwicker loudness, sharpness, roughness | Only free/open-source implementation of ISO 532-1, DIN 45692 |
| pyloudnorm | 0.1.1 | LUFS loudness (ITU-R BS.1770-4) | Already in use, standard-compliant |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| librosa | 0.11.0 | Audio resampling to 48kHz | Preprocessing for MoSQITo |
| scipy.signal | 1.14+ | Resampling alternative | If librosa resampling has issues |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MoSQITo | Soundscapy | More ergonomic API but heavier dependency chain; designed for soundscape research, overkill for single-file analysis |
| MoSQITo | PyAnsys Sound | Cleaner API but commercial focus, potential licensing issues |
| MoSQITo | Custom implementation | Zwicker algorithms are complex (ISO 532-1 is 50+ pages), validation is critical |

**Installation:**
```bash
# MoSQITo as optional dependency
pip install mosqito>=1.2.0

# Already installed
pip install pyloudnorm>=0.1.0
pip install librosa>=0.10.0
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Integration Structure
```
src/audioloop/
├── analyze.py           # Existing - add psychoacoustic section
├── psychoacoustic.py    # NEW - MoSQITo wrapper with preprocessing
└── errors.py            # Existing - add PsychoacousticError
```

### Pattern 1: Lazy Import with Graceful Fallback
**What:** Import MoSQITo only when psychoacoustic features are requested
**When to use:** Optional heavy dependencies that may not be installed
**Example:**
```python
def compute_psychoacoustic(y: np.ndarray, sr: int) -> dict | None:
    """Compute psychoacoustic metrics if MoSQITo available."""
    try:
        from mosqito.sq_metrics import loudness_zwtv, sharpness_din_from_loudness, roughness_dw
    except ImportError:
        return None  # MoSQITo not installed

    # Preprocess: resample to 48kHz mono
    y_48k = librosa.resample(y, orig_sr=sr, target_sr=48000)
    if y_48k.ndim > 1:
        y_48k = np.mean(y_48k, axis=0)  # Convert to mono

    # Compute metrics
    N, N_spec, bark_axis, time_axis = loudness_zwtv(y_48k, 48000, field_type="free")
    S = sharpness_din_from_loudness(N, N_spec, is_stationary=False)
    R, time_axis_r, _, _ = roughness_dw(y_48k, 48000)

    return {
        "loudness_sone": float(np.mean(N)),
        "sharpness_acum": float(np.mean(S)),
        "roughness_asper": float(np.mean(R)),
    }
```

### Pattern 2: Preprocessing Pipeline
**What:** Standardize audio format before MoSQITo analysis
**When to use:** Always - MoSQITo has strict requirements
**Example:**
```python
def prepare_for_mosqito(y: np.ndarray, sr: int) -> tuple[np.ndarray, int]:
    """Convert audio to MoSQITo-compatible format (48kHz mono).

    Args:
        y: Audio signal (mono or stereo)
        sr: Original sample rate

    Returns:
        Tuple of (resampled mono signal, 48000)
    """
    # Resample to 48kHz
    if sr != 48000:
        y = librosa.resample(y, orig_sr=sr, target_sr=48000)

    # Convert to mono if stereo
    if y.ndim > 1:
        y = np.mean(y, axis=0)

    # Ensure float32 for MoSQITo
    y = y.astype(np.float32)

    return y, 48000
```

### Pattern 3: Aggregating Time-Varying Results
**What:** MoSQITo returns time-varying values; summarize for Claude
**When to use:** Always - raw time series is too verbose
**Example:**
```python
def summarize_metric(values: np.ndarray, name: str) -> dict:
    """Summarize time-varying psychoacoustic metric."""
    return {
        f"{name}_mean": float(np.mean(values)),
        f"{name}_max": float(np.max(values)),
        f"{name}_n5": float(np.percentile(values, 95)),  # Loudness uses N5 (95th percentile)
    }
```

### Anti-Patterns to Avoid
- **Writing to temp files:** MoSQITo can work with numpy arrays directly via `loudness_zwtv()` function, not just the Audio class
- **Ignoring sample rate:** MoSQITo silently produces wrong results if not 48kHz
- **Processing stereo directly:** MoSQITo expects mono; average channels first
- **Using Audio class for simple cases:** The `loudness_zwtv()`, `sharpness_din_from_loudness()`, `roughness_dw()` functions are simpler than the Audio class
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Zwicker loudness | Time-domain energy calculation | MoSQITo `loudness_zwtv` | ISO 532-1 algorithm has 50+ pages of spec, critical band filtering, temporal masking |
| Roughness | Modulation index calculation | MoSQITo `roughness_dw` | Daniel & Weber model validated against psychoacoustic experiments |
| Sharpness | High-frequency energy weighting | MoSQITo `sharpness_din_from_loudness` | DIN 45692 requires specific loudness as input, complex weighting function |
| LUFS loudness | RMS with K-weighting | pyloudnorm | ITU-R BS.1770-4 compliance requires specific filter coefficients and gating |
| Audio resampling | Linear interpolation | librosa.resample | Proper anti-aliasing filter required for accurate spectral content |

**Key insight:** Psychoacoustic metrics attempt to model human perception. They're validated against listening experiments with specific algorithms. A "close enough" approximation produces misleading data - either use the validated implementation or don't report the metric.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Wrong Sample Rate
**What goes wrong:** MoSQITo silently produces incorrect values if audio isn't 48kHz
**Why it happens:** No runtime validation in MoSQITo; it assumes correct input
**How to avoid:** Always resample to 48kHz before passing to MoSQITo, assert sample rate
**Warning signs:** Loudness values that don't match perceptual experience; values outside normal ranges

### Pitfall 2: Stereo Input to MoSQITo
**What goes wrong:** MoSQITo expects mono; stereo causes shape errors or wrong results
**Why it happens:** Audio analysis often uses stereo; easy to forget conversion
**How to avoid:** Convert to mono by averaging channels before MoSQITo
**Warning signs:** Shape mismatch errors, or doubled loudness values

### Pitfall 3: Slow Computation Blocking CLI
**What goes wrong:** `audioloop analyze` takes 1+ minute for psychoacoustic metrics
**Why it happens:** MoSQITo is computationally expensive (50s+ for 30s audio)
**How to avoid:** Consider `--no-psychoacoustic` flag, or compute in parallel, or show progress
**Warning signs:** User thinks CLI is frozen; interrupts mid-computation

### Pitfall 4: Confusing Zwicker Loudness and LUFS
**What goes wrong:** Reporting wrong unit or misinterpreting values
**Why it happens:** Two different "loudness" measurements with different scales
**How to avoid:** Always label clearly: "loudness_sone" vs "loudness_lufs"; include units in output
**Warning signs:** Loudness in sones being compared to dB LUFS targets

### Pitfall 5: Missing Optional Dependency
**What goes wrong:** ImportError crashes the analyze command
**Why it happens:** MoSQITo is optional but code assumes it's installed
**How to avoid:** Graceful fallback - return `null` for psychoacoustic metrics if MoSQITo unavailable
**Warning signs:** "ModuleNotFoundError: No module named 'mosqito'"

### Pitfall 6: Calibration Complexity
**What goes wrong:** Absolute loudness values meaningless without calibration
**Why it happens:** MoSQITo expects calibrated input (dBFS to dBSPL mapping)
**How to avoid:** For relative comparison (our use case), use `calib=1.0`; document that values are relative
**Warning signs:** Users expecting "correct" absolute loudness in sones
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from research:

### MoSQITo Direct Function API (Preferred)
```python
# Source: MoSQITo docs, miniDSP tutorial
from mosqito.sq_metrics import loudness_zwtv, sharpness_din_from_loudness, roughness_dw
import numpy as np
import librosa

# Load and preprocess
y, sr = librosa.load("audio.wav", sr=48000, mono=True)

# Compute Zwicker loudness (time-varying)
# Returns: N (loudness array), N_spec (specific loudness), bark_axis, time_axis
N, N_spec, bark_axis, time_axis = loudness_zwtv(y, fs=48000, field_type="free")
# field_type: "free" for free-field, "diffuse" for diffuse-field

# Compute sharpness from loudness (DIN 45692)
S = sharpness_din_from_loudness(N, N_spec, is_stationary=False)

# Compute roughness (Daniel & Weber model)
R, time_axis_r, _, _ = roughness_dw(y, fs=48000)

# Summarize for output
results = {
    "loudness_sone": float(np.mean(N)),      # Average loudness in sones
    "loudness_sone_max": float(np.max(N)),   # Peak loudness
    "sharpness_acum": float(np.mean(S)),     # Average sharpness in acum
    "roughness_asper": float(np.mean(R)),    # Average roughness in asper
}
```

### MoSQITo Audio Class API (Alternative)
```python
# Source: MoSQITo tutorials
from mosqito.classes.Audio import Audio

# Load audio file directly
signal = Audio("/path/to/48khz_mono.wav", calib=1.0)

# Compute metrics via class methods
signal.compute_loudness(field_type="free")
signal.compute_sharpness(method="din", skip=0.2)
signal.compute_roughness()

# Access results
loudness = signal.loudness_zwicker  # SciDataTool Data object
sharpness = signal.sharpness["din"]
roughness = signal.roughness["Daniel Weber"]
```

### pyloudnorm LUFS (Already Integrated)
```python
# Source: pyloudnorm README, Context7
import soundfile as sf
import pyloudnorm as pyln

data, rate = sf.read("audio.wav")
meter = pyln.Meter(rate)
loudness_lufs = meter.integrated_loudness(data)  # dB LUFS
```

### Integration into Existing analyze.py
```python
# Pattern for adding to existing AnalysisResult
@dataclass
class AnalysisResult:
    # ... existing fields ...
    psychoacoustic: dict = field(default_factory=dict)  # NEW

def analyze(path: Path) -> AnalysisResult:
    # ... existing analysis ...

    # Add psychoacoustic if available
    psychoacoustic = compute_psychoacoustic_if_available(y, sr)

    return AnalysisResult(
        # ... existing ...
        psychoacoustic=psychoacoustic or {},
    )
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ECMA-418-1 loudness | ISO 532-1 (Zwicker) via MoSQITo | Ongoing | MoSQITo implements ISO 532-1:2017; ECMA-418-2 roughness in development |
| No open-source option | MoSQITo 1.2.1 | 2024 | First free Python implementation of full Zwicker metric suite |
| Soundscapy required | Direct MoSQITo | 2024 | MoSQITo now has cleaner direct API; Soundscapy adds complexity |

**New tools/patterns to consider:**
- **ECMA-418-2 roughness:** New standard (2022) with hearing model; MoSQITo implementation in development (as of late 2024)
- **Soundscapy 0.7+:** Good for batch processing binaural recordings; overkill for single-file CLI

**Deprecated/outdated:**
- **MoSQITo Audio class for simple cases:** Direct functions (`loudness_zwtv`, etc.) are now preferred
- **Fluctuation strength expectations:** Not implemented in any free Python library; skip for now
</sota_updates>

<open_questions>
## Open Questions

Things that need resolution during planning/implementation:

1. **Performance strategy**
   - What we know: MoSQITo takes 50+ seconds for 30s audio
   - What's unclear: Is this acceptable for CLI UX? Should we parallelize? Add progress indicator?
   - Recommendation: Add `--no-psychoacoustic` flag for quick analysis; show progress spinner

2. **Error handling for invalid audio**
   - What we know: Very short or silent audio may cause MoSQITo errors
   - What's unclear: Exact failure modes and thresholds
   - Recommendation: Test with edge cases during implementation; add try/catch with informative errors

3. **Output schema evolution**
   - What we know: Need to add `psychoacoustic` section to JSON output
   - What's unclear: Should this be nested or flat? Include time series?
   - Recommendation: Nested with summary stats only (mean, max, N5); time series too verbose
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [MoSQITo GitHub](https://github.com/Eomys/MoSQITo) - Main repository, version 1.2.1
- [MoSQITo PyPI](https://pypi.org/project/mosqito/) - Package info, Python >=3.5
- [pyloudnorm GitHub](https://github.com/csteinmetz1/pyloudnorm) - ITU-R BS.1770-4 implementation
- [Context7 /csteinmetz1/pyloudnorm](https://context7.com) - API examples verified

### Secondary (MEDIUM confidence)
- [miniDSP MoSQITo Tutorial](https://www.minidsp.com/applications/acoustic-measurements/psychoacoustic-measurements-with-mosqito) - API examples, 48kHz requirement confirmed
- [Soundscapy Documentation](https://soundscapy.readthedocs.io/) - Integration patterns, performance notes
- [MoSQITo-FDP Documentation](https://github.com/djcaminero/MoSQITo-FDP) - Loudness validation details

### Tertiary (LOW confidence - needs validation during implementation)
- Exact performance numbers (50s+ for 30s audio) - from Soundscapy docs, may vary
- Edge case behavior with very short audio - not fully documented
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: MoSQITo for Zwicker psychoacoustics
- Ecosystem: pyloudnorm (LUFS), librosa (resampling)
- Patterns: Lazy import, preprocessing pipeline, graceful fallback
- Pitfalls: Sample rate, stereo, performance, calibration

**Confidence breakdown:**
- Standard stack: HIGH - MoSQITo is the only free option, well-documented
- Architecture: HIGH - Integration patterns clear from existing code and MoSQITo docs
- Pitfalls: HIGH - Well-documented in miniDSP tutorial and Soundscapy
- Code examples: MEDIUM - Based on docs, not tested locally yet

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - MoSQITo ecosystem stable)
</metadata>

---

*Phase: 04-zwicker-integration*
*Research completed: 2026-01-09*
*Ready for planning: yes*
