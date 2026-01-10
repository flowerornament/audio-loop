# Phase 2: Analysis Pipeline - Research

## Executive Summary

Phase 2 requires building an audio analysis pipeline with librosa-based feature extraction and Zwicker psychoacoustic metrics. Research reveals a clear standard stack:

- **librosa** (0.11.0) for spectral/temporal features (well-documented, mature)
- **MoSQITo** (1.2.1) for psychoacoustic metrics (roughness, sharpness, loudness)
- **pyloudnorm** for LUFS loudness measurement
- **sparklines** package for terminal visualization
- **rich** for formatted CLI output

Key findings:
- **MoSQITo requires 48kHz mono audio** - preprocessing step needed
- **Fluctuation strength is NOT implemented in MoSQITo** - only loudness, sharpness, roughness available
- **Soundscapy** is a newer option that wraps MoSQITo with better ergonomics for binaural analysis
- **librosa 0.11.0** (March 2025) has full Python 3.13 support and type annotations

**Temporal analysis** (for sounds evolving over 5-60 seconds):
- **Beat/tempo tracking** via librosa.beat (single tempo or time-varying via PLP)
- **Pitch tracking** via pYIN (librosa) or CREPE (neural, state-of-the-art)
- **Feature evolution** via delta coefficients and trajectory summarization
- **Modulation detection** via FFT of feature time series (LFO detection)
- **Segmentation** via recurrence matrices and agglomerative clustering

---

## 1. Audio Analysis Library Ecosystem

### Primary Stack

| Library | Purpose | Version | Notes |
|---------|---------|---------|-------|
| **librosa** | Spectral, temporal, pitch features | 0.11.0 (Mar 2025) | Industry standard, full type annotations |
| **MoSQITo** | Zwicker psychoacoustic metrics | 1.2.1 (Apr 2024) | 48kHz mono requirement, no fluctuation strength |
| **pyloudnorm** | LUFS loudness (ITU-R BS.1770-4) | 0.1.1 | Simple API, NumPy-only deps |
| **scipy.signal** | Low-level DSP, stereo coherence | 1.14+ | Use for mid/side and correlation |
| **Soundscapy** | Binaural/soundscape analysis | 0.7.8 | Wraps MoSQITo, adds acoustic indices |

### Alternatives Considered

| Library | Why Not Primary |
|---------|-----------------|
| **Essentia** | More powerful but steeper learning curve, C++ bindings complexity |
| **pyAudioAnalysis** | Less actively maintained, classification-focused |
| **PyAnsys Sound** | Commercial focus, licensing implications |
| **scikit-maad** | Ecological soundscape focus, less relevant for synthesis |

### Decision: Use librosa + MoSQITo + pyloudnorm

librosa handles the bulk of features we need. MoSQITo provides the Zwicker metrics that librosa lacks. pyloudnorm gives proper LUFS measurement. This combination covers all requirements without over-engineering.

---

## 2. Feature Extraction Architecture

### librosa Features (Standard)

```python
import librosa
import numpy as np

# Load audio (IMPORTANT: set sr=None for native rate, or explicit rate)
y, sr = librosa.load('audio.wav', sr=None)

# Spectral features
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
flatness = librosa.feature.spectral_flatness(y=y)
bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
flux = librosa.onset.onset_strength(y=y, sr=sr)

# Pitch/harmonicity
f0, voiced_flag, voiced_probs = librosa.pyin(
    y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7')
)

# Rhythm
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)

# MFCCs
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
```

### Stereo Analysis (scipy + numpy)

```python
import numpy as np
from scipy.signal import coherence

def analyze_stereo(left, right, sr):
    # Mid/Side
    mid = (left + right) / 2
    side = (left - right) / 2

    # Stereo width (energy ratio)
    mid_energy = np.sum(mid**2)
    side_energy = np.sum(side**2)
    width = side_energy / (mid_energy + side_energy + 1e-10)

    # Phase correlation (-1 to +1)
    correlation = np.corrcoef(left, right)[0, 1]

    # Frequency-domain coherence
    freqs, coh = coherence(left, right, fs=sr)

    return {
        'stereo_width': width,
        'lr_correlation': correlation,
        'coherence': coh
    }
```

### Envelope/Dynamics Analysis

```python
def analyze_envelope(y, sr):
    # RMS energy
    rms = librosa.feature.rms(y=y)[0]

    # Crest factor (peak to RMS ratio)
    peak = np.max(np.abs(y))
    rms_overall = np.sqrt(np.mean(y**2))
    crest_factor = peak / (rms_overall + 1e-10)

    # Attack time estimation (time to reach 90% of peak)
    envelope = np.abs(y)
    threshold = 0.9 * peak
    attack_samples = np.argmax(envelope >= threshold)
    attack_time = attack_samples / sr

    return {
        'rms': rms_overall,
        'crest_factor': crest_factor,
        'attack_time_ms': attack_time * 1000
    }
```

---

## 2.5 Temporal Evolution Analysis (NEW)

For sounds that evolve over 5-60 seconds (pads, textures, sequences), we need to analyze change over time, not just instantaneous features.

### Beat and Tempo Detection

```python
import librosa

y, sr = librosa.load('audio.wav', sr=None)

# Basic tempo and beat tracking
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# For time-varying tempo, use PLP (Predominant Local Pulse)
pulse = librosa.beat.plp(y=y, sr=sr)

# Tempogram for visualizing tempo over time
tempogram = librosa.feature.tempogram(y=y, sr=sr)
```

**Key parameters:**
- `start_bpm`: Initial tempo guess (default 120)
- `tightness`: How strictly to follow tempo (higher = stricter)
- `trim`: Set False if no silence at end of file

**Accuracy notes:** Beat tracker assumes single average tempo. For varying tempo, use `plp` or provide time-varying tempo estimates.

### Pitch Tracking (F0 Contours)

Two main approaches:

**pYIN (in librosa)** - Good accuracy, pure DSP:
```python
# pYIN pitch tracking with confidence
f0, voiced_flag, voiced_probs = librosa.pyin(
    y,
    fmin=librosa.note_to_hz('C2'),  # ~65 Hz
    fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
    sr=sr
)

# f0 is pitch in Hz (NaN for unvoiced frames)
# voiced_probs gives confidence per frame
```

**CREPE (neural network)** - State-of-the-art accuracy, requires TensorFlow:
```python
import crepe

# Returns time, frequency, confidence, activation
time, frequency, confidence, activation = crepe.predict(
    y, sr,
    model_capacity='medium',  # tiny/small/medium/large/full
    viterbi=True  # Smooth with Viterbi decoding
)
```

**Comparison:**
| Method | Accuracy | Speed | Dependencies |
|--------|----------|-------|--------------|
| pYIN | Good | Fast | librosa only |
| CREPE | Best | Slower | TensorFlow |

**Recommendation:** Start with pYIN. Add CREPE as optional if pitch accuracy is critical.

### Feature Evolution (Delta Coefficients)

Track how features change over time using derivatives:

```python
# Compute spectral centroid over time
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

# First derivative (rate of change)
centroid_delta = librosa.feature.delta(centroid.reshape(1, -1), order=1)[0]

# Second derivative (acceleration of change)
centroid_delta2 = librosa.feature.delta(centroid.reshape(1, -1), order=2)[0]

# Summarize evolution
evolution_stats = {
    'centroid_mean': np.mean(centroid),
    'centroid_std': np.std(centroid),  # How much it varies
    'centroid_delta_mean': np.mean(centroid_delta),  # Average rate of change
    'centroid_range': np.max(centroid) - np.min(centroid),  # Total sweep
}
```

### Spectral Flux (Change Detection)

Measures how much the spectrum changes frame-to-frame:

```python
# Onset strength = spectral flux
onset_env = librosa.onset.onset_strength(y=y, sr=sr)

# Detect discrete onset events
onset_frames = librosa.onset.onset_detect(y=y, sr=sr, onset_envelope=onset_env)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)

# Summarize activity
activity_stats = {
    'onset_count': len(onset_frames),
    'onset_rate_per_sec': len(onset_frames) / librosa.get_duration(y=y, sr=sr),
    'flux_mean': np.mean(onset_env),
    'flux_std': np.std(onset_env),
}
```

### Segment Detection

Find distinct sections in evolving sounds:

```python
# Use chroma features for harmonic segmentation
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

# Self-similarity matrix
R = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)

# Agglomerative clustering for segment boundaries
# k=None lets it auto-determine number of segments
bound_frames = librosa.segment.agglomerative(chroma, k=None)
bound_times = librosa.frames_to_time(bound_frames, sr=sr)
```

### Modulation/LFO Detection

Detect periodic modulation in features (e.g., filter sweep, tremolo):

```python
from scipy.signal import find_peaks
from scipy.fft import rfft, rfftfreq

def detect_modulation(feature_series, sr, hop_length=512):
    """Detect periodic modulation in a feature time series."""
    # Feature frame rate
    frame_rate = sr / hop_length

    # FFT of the feature trajectory
    spectrum = np.abs(rfft(feature_series - np.mean(feature_series)))
    freqs = rfftfreq(len(feature_series), 1/frame_rate)

    # Find peaks in modulation spectrum (0.1-20 Hz = typical LFO range)
    lfo_mask = (freqs >= 0.1) & (freqs <= 20)
    peaks, props = find_peaks(spectrum[lfo_mask], height=np.max(spectrum) * 0.1)

    if len(peaks) > 0:
        peak_idx = peaks[np.argmax(props['peak_heights'])]
        mod_freq = freqs[lfo_mask][peak_idx]
        mod_depth = props['peak_heights'][np.argmax(props['peak_heights'])]
        return {'modulation_hz': mod_freq, 'modulation_depth': mod_depth}
    return {'modulation_hz': None, 'modulation_depth': 0}

# Example: detect filter modulation via centroid
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
mod_info = detect_modulation(centroid, sr)
```

### Trajectory Summarization

For Claude to understand feature evolution, summarize trajectories:

```python
def summarize_trajectory(values, times=None):
    """Summarize how a feature evolves over time."""
    return {
        'start': float(values[0]),
        'end': float(values[-1]),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'trend': 'rising' if values[-1] > values[0] * 1.1 else
                 'falling' if values[-1] < values[0] * 0.9 else 'stable',
        'range_ratio': float((np.max(values) - np.min(values)) / (np.mean(values) + 1e-10)),
    }

# Example output for centroid:
# {
#   "start": 1200,
#   "end": 400,
#   "trend": "falling",  # Filter closing over time
#   "range_ratio": 0.8   # Significant movement
# }
```

### Recommended Temporal Features for Claude

| Feature | What It Tells Claude | When Useful |
|---------|---------------------|-------------|
| tempo_bpm | Rhythmic pulse | Beats, sequences |
| beat_count | Number of beats | Rhythmic content |
| onset_rate | Events per second | Percussive vs sustained |
| f0_contour | Pitch over time | Melodic content |
| centroid_trajectory | Brightness evolution | Filter sweeps |
| centroid_delta_mean | Rate of timbral change | Evolving textures |
| segment_count | Distinct sections | Complex structures |
| modulation_hz | LFO rate if present | Wobble, tremolo |

---

## 3. Zwicker Psychoacoustic Metrics

### MoSQITo Library

**Critical constraint**: MoSQITo requires **48kHz sample rate** and **mono** audio.

#### Available Metrics (as of v1.2.1)

| Metric | Implementation | Reference | Status |
|--------|---------------|-----------|--------|
| Loudness | ISO 532-1 | Stationary and time-varying | ✅ Implemented |
| Sharpness | DIN 45692, Aures, Bismarck, Fastl | Multiple weighting options | ✅ Implemented |
| Roughness | Daniel & Weber (1997) | Validated implementation | ✅ Implemented |
| Fluctuation Strength | - | - | ❌ **NOT implemented** |
| Tonality | MoSQITo-FDP fork | In development | ⚠️ Experimental fork only |

**Important:** Fluctuation strength (slow modulation perception, 0.5-20 Hz) is NOT available in MoSQITo. If needed, consider:
- Implementing a basic modulation index calculation manually
- Using amplitude envelope analysis as a proxy
- Skipping this metric for v1

#### Usage Pattern

```python
from mosqito.classes.Audio import Audio

# Load and prepare audio (must be 48kHz mono!)
audio = Audio(
    "path/to/audio.wav",
    calib=1.0,  # calibration factor
)

# Sharpness (DIN 45692)
audio.compute_sharpness(method="din", skip=0.2)
sharpness = audio.sharpness["din"]

# Roughness
audio.compute_roughness()
roughness = audio.roughness

# Loudness
audio.compute_loudness()
loudness = audio.loudness  # in sones
```

#### Preprocessing for MoSQITo

```python
import librosa
import soundfile as sf

def prepare_for_mosqito(input_path, output_path):
    """Convert audio to 48kHz mono for MoSQITo analysis."""
    y, sr = librosa.load(input_path, sr=48000, mono=True)
    sf.write(output_path, y, 48000)
    return output_path
```

### Alternative: PyAnsys Sound

If MoSQITo doesn't meet needs, PyAnsys Sound offers similar metrics with a cleaner API:

```python
from ansys.sound.core import Roughness, Sharpness, FluctuationStrength

roughness = Roughness(signal=signal)
roughness.process()
value = roughness.get_roughness()  # in asper
```

However, PyAnsys may have licensing implications - verify before using.

---

## 4. LUFS Loudness Measurement

### pyloudnorm

Standard-compliant loudness measurement (ITU-R BS.1770-4):

```python
import soundfile as sf
import pyloudnorm as pyln

# Load audio
data, rate = sf.read("audio.wav")

# Create meter
meter = pyln.Meter(rate)

# Measure integrated loudness
loudness = meter.integrated_loudness(data)  # dB LUFS

# Loudness Range (LRA) - EBU Tech 3342
# (check if pyloudnorm supports this directly)
```

**Note**: LUFS is different from Zwicker loudness (sones). Both are useful:
- LUFS: Technical loudness for broadcast compliance
- Sones: Perceptual loudness matching human hearing

---

## 5. ASCII Spectrogram Approaches

### Options Evaluated

| Option | Verdict |
|--------|---------|
| spectriclabs/ascii_spectrogram | Minimal, labeled "toy" - not suitable |
| sparklines package | Good for 1D time series, not 2D spectrograms |
| Custom implementation | Recommended - simple to build |

### Recommended: Custom Implementation

Build a simple spectrogram-to-Unicode converter:

```python
import numpy as np
import librosa

BLOCKS = ' ▁▂▃▄▅▆▇█'  # Unicode block elements (9 levels)

def ascii_spectrogram(y, sr, n_fft=2048, hop_length=512, n_mels=20, width=80):
    """Generate ASCII spectrogram from audio."""
    # Compute mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft,
                                        hop_length=hop_length, n_mels=n_mels)
    S_db = librosa.power_to_db(S, ref=np.max)

    # Normalize to 0-1
    S_norm = (S_db - S_db.min()) / (S_db.max() - S_db.min() + 1e-10)

    # Resample time axis to fit width
    n_frames = S_norm.shape[1]
    if n_frames > width:
        indices = np.linspace(0, n_frames - 1, width, dtype=int)
        S_norm = S_norm[:, indices]

    # Convert to ASCII (flip so low freq at bottom)
    lines = []
    for row in S_norm[::-1]:  # Reverse for low freq at bottom
        line = ''.join(BLOCKS[int(v * (len(BLOCKS) - 1))] for v in row)
        lines.append(line)

    return '\n'.join(lines)
```

### sparklines Package (for 1D data)

Useful for envelope visualization, not spectrograms:

```python
from sparklines import sparklines

# Generate sparkline for RMS envelope
rms = librosa.feature.rms(y=y)[0]
rms_downsampled = rms[::len(rms)//40]  # 40 characters wide
sparkline = sparklines(rms_downsampled.tolist())[0]
print(f"Envelope: {sparkline}")
# Output: Envelope: ▁▂▄▇███▇▆▅▄▃▂▁
```

---

## 6. CLI Design Patterns

### Recommended Stack

- **typer** - Type-hint based CLI framework (already in PROJECT.md)
- **rich** - Terminal formatting, tables, colors
- **orjson** - Fast JSON serialization (for `--json` output)

### Output Design Pattern

```python
import typer
from rich.console import Console
from rich.table import Table
import orjson

app = typer.Typer()
console = Console()

@app.command()
def analyze(
    file: str,
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Analyze audio file and display features."""
    results = run_analysis(file)

    if json_output:
        # Structured output for Claude parsing
        print(orjson.dumps(results).decode())
    else:
        # Human-readable with interpretation
        display_rich_output(results, verbose)

def display_rich_output(results, verbose):
    console.print("[bold]SPECTRAL PROFILE[/bold]")
    console.print(f"  Centroid: {results['centroid']:.0f} Hz "
                  f"({interpret_centroid(results['centroid'])})")
    # ... etc
```

### JSON Schema for Claude Parsing

```json
{
  "file": "sound.wav",
  "duration_sec": 30.0,
  "sample_rate": 48000,
  "spectral": {
    "centroid_hz": 847,
    "centroid_interpretation": "warm territory - typical pads 500-1500Hz",
    "rolloff_hz": 2100,
    "flatness": 0.12,
    "bandwidth_hz": 1200
  },
  "dynamics": {
    "attack_ms": 48,
    "rms": 0.23,
    "crest_factor": 4.2
  },
  "psychoacoustic": {
    "roughness_asper": 0.23,
    "sharpness_acum": 0.8,
    "loudness_sone": 12.5,
    "loudness_lufs": -14.2
  },
  "rhythm": {
    "tempo_bpm": 120,
    "beat_count": 60,
    "onset_count": 45,
    "onset_rate_per_sec": 1.5
  },
  "pitch": {
    "f0_mean_hz": 220,
    "f0_std_hz": 12,
    "pitched_ratio": 0.85,
    "pitch_trend": "stable"
  },
  "evolution": {
    "centroid_trend": "falling",
    "centroid_start_hz": 1200,
    "centroid_end_hz": 400,
    "centroid_delta_mean": -26.7,
    "modulation_detected": true,
    "modulation_hz": 0.5,
    "segment_count": 3
  },
  "stereo": {
    "width": 0.72,
    "correlation": 0.85
  }
}
```

The `evolution` section captures how the sound changes over its duration - essential for pads, textures, and sequences.

---

## 7. Common Pitfalls

### librosa

| Pitfall | Solution |
|---------|----------|
| Default resample to 22050 Hz | Always use `sr=None` or explicit rate |
| Slow loading | Use `res_type='kaiser_fast'` for speed |
| Spurious centroid at silence | Add small constant before computing |
| Frame size for speech vs music | Use n_fft=512 for speech, 2048 for music |
| Memory with long files | Process in chunks or use streaming |

### MoSQITo

| Pitfall | Solution |
|---------|----------|
| Sample rate must be 48kHz | Resample before analysis |
| Must be mono | Convert stereo to mono |
| Fluctuation strength may be missing | Verify availability, have fallback |
| Calibration complexity | Use calib=1.0 for relative comparison |

### General Audio Analysis

| Pitfall | Solution |
|---------|----------|
| Different sample rates across files | Standardize early in pipeline |
| Stereo vs mono inconsistency | Decide mono strategy upfront |
| Floating point normalization | Use consistent range (-1 to 1) |
| Silent/clipped audio | Add detection and warnings |

---

## 8. What NOT to Hand-Roll

| Feature | Use Instead | Why |
|---------|-------------|-----|
| Spectral features | librosa | Optimized, validated |
| Zwicker loudness/sharpness/roughness | MoSQITo | Complex algorithms, needs validation |
| LUFS measurement | pyloudnorm | Standard-compliant, tested |
| Resampling | librosa.resample | Correct anti-aliasing |
| Pitch tracking | librosa.pyin | State-of-the-art algorithm |
| Beat tracking | librosa.beat.beat_track | Dynamic programming, tuned |

### Safe to Implement Custom

- ASCII spectrogram (simple conversion)
- Stereo width/correlation (basic math)
- Envelope attack detection (simple threshold)
- Interpretation layer ("warm territory" text)
- Feature aggregation (mean, std over time)

---

## 9. Architecture Recommendation

```
audioloop analyze <file.wav>
         │
         ▼
┌─────────────────────────────────────┐
│  Preprocessing                       │
│  - Load with librosa (native sr)    │
│  - Split stereo channels            │
│  - Create 48kHz mono for MoSQITo    │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Feature Extraction (parallel)       │
│  ├── Spectral (librosa)             │
│  │   └── centroid, rolloff, flux    │
│  ├── Dynamics (librosa + numpy)     │
│  │   └── RMS, attack, crest factor  │
│  ├── Pitch (librosa.pyin)           │
│  │   └── f0 contour, voiced ratio   │
│  ├── Rhythm (librosa.beat)          │
│  │   └── tempo, beats, onsets       │
│  ├── Evolution (NEW)                │
│  │   └── delta coefficients         │
│  │   └── trajectory stats           │
│  │   └── modulation detection       │
│  │   └── segment boundaries         │
│  ├── Stereo (scipy + numpy)         │
│  ├── Psychoacoustic (MoSQITo)       │
│  └── LUFS (pyloudnorm)              │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Interpretation Layer                │
│  - Add context to raw values        │
│  - Compare to typical ranges        │
│  - Describe evolution trends        │
│  - Generate descriptive text        │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Output Formatting                   │
│  - JSON (--json) for Claude         │
│  - Rich tables + sparklines (human) │
│  - ASCII spectrogram                │
│  - Feature trajectory plots (opt)   │
└─────────────────────────────────────┘
```

---

## 10. Dependencies Summary

```toml
[project]
dependencies = [
    "librosa>=0.10.0,<0.12",  # 0.11.0 is current, has full type annotations
    "mosqito>=1.2.0",         # 1.2.1 is current (Apr 2024)
    "pyloudnorm>=0.1.0",      # LUFS measurement
    "typer>=0.9.0",           # CLI framework
    "rich>=13.0.0",           # Terminal formatting
    "sparklines>=0.4.0",      # 1D visualizations
    "orjson>=3.9.0",          # Fast JSON (optional, stdlib json works too)
    "soundfile>=0.12.0",      # Audio file I/O
    "numpy>=1.24.0",
    "scipy>=1.10.0",
]

[project.optional-dependencies]
pitch = [
    "crepe>=0.0.16",          # Neural pitch tracking (requires TensorFlow)
]
```

**Note on librosa 0.11.0:** Requires Python 3.9+. Windows users with Python 3.13 may have issues with optional `samplerate` backend - use default resampling settings.

**Note on CREPE:** Only needed if pYIN pitch tracking isn't accurate enough. Requires TensorFlow, which is heavy. Start without it.

---

## 11. Soundscapy Alternative

**Soundscapy** (v0.7.8) is a newer library that wraps MoSQITo with better ergonomics:

```python
from soundscapy.audio import Binaural, AnalysisSettings

# Load binaural recording
b = Binaural.from_wav("audio.wav")

# Compute psychoacoustic metrics
settings = AnalysisSettings()
results = b.psychoacoustic_analysis(settings)
```

### Pros
- Cleaner API for binaural analysis
- Configurable via YAML settings files
- ISO 12913-3 compliant
- Combines acoustics, maad, and MoSQITo

### Cons
- Larger dependency footprint
- Designed for soundscape research, not synthesis feedback
- May be overkill for our single-file analysis use case

**Recommendation:** Start with direct MoSQITo use. Consider Soundscapy if we need binaural support later.

---

## 12. Open Questions for Planning

1. ~~**MoSQITo fluctuation strength**: Verify if implemented.~~ **RESOLVED: NOT implemented. Skip for v1.**

2. ~~**Sample rate strategy**: Standardize on 48kHz throughout (for MoSQITo compat) or use native rate and resample only for psychoacoustic?~~ **RESOLVED: Use native sample rate for v1. Resample only when MoSQITo is added in Milestone 2.**

3. ~~**Stereo handling**: Analyze both channels separately, or convert to mid/side, or force mono?~~ **RESOLVED: Analyze both L/R channels separately, compute per-channel features, report deltas between channels. Also compute stereo width and correlation.**

4. **Spectrogram resolution**: How many mel bands? How wide should ASCII output be? *(Deferred - spectrogram is post-v1)*

5. ~~**Interpretation thresholds**: What centroid values map to "warm" vs "bright"? Need calibration or use literature values?~~ **RESOLVED: No hardcoded thresholds. Provide reference ranges in output (e.g., "typical pads: 500-1500Hz"). Let Claude learn through iteration.**

6. ~~**Fluctuation strength alternative**: Implement basic modulation index, or skip entirely for v1?~~ **RESOLVED: Skip for v1. Temporal evolution features (beat tracking, modulation detection) are also deferred.**

---

## Sources

### Core Libraries
- [librosa Documentation](https://librosa.org/doc/main/)
- [librosa 0.11.0 Changelog](https://librosa.org/doc/0.11.0/changelog.html)
- [librosa Beat and Tempo](https://librosa.org/doc/main/beat.html)
- [librosa.feature.delta](https://librosa.org/doc/main/generated/librosa.feature.delta.html)
- [MoSQITo GitHub](https://github.com/Eomys/MoSQITo)
- [MoSQITo ReadTheDocs](https://mosqito.readthedocs.io/)
- [MoSQITo PyPI](https://pypi.org/project/mosqito/)
- [pyloudnorm GitHub](https://github.com/csteinmetz1/pyloudnorm)

### Pitch Tracking
- [CREPE GitHub](https://github.com/marl/crepe) - Neural pitch estimation
- [CREPE Paper (ICASSP 2018)](https://arxiv.org/abs/1802.06182)

### Temporal Analysis
- [Tempo, Beat and Downbeat Tutorial](https://tempobeatdownbeat.github.io/tutorial/ch2_basics/evaluate.html)
- [Spectral Novelty Functions](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S1_NoveltySpectral.html)
- [Onset Detection (AudioLabs)](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C6/C6S1_OnsetDetection.html)
- Ellis, D.P.W. (2007): "Beat tracking by dynamic programming", Journal of New Music Research

### Other
- [Soundscapy Documentation](https://soundscapy.readthedocs.io/)
- [Soundscapy Binaural Analysis Tutorial](https://soundscapy.readthedocs.io/en/docs/tutorials/BinauralAnalysis/)
- [PyAnsys Sound Examples](https://sound.docs.pyansys.com/version/stable/examples/gallery_examples/007_calculate_psychoacoustic_indicators.html)
- [sparklines PyPI](https://pypi.org/project/sparklines/)
- [MiniDSP MoSQITo Tutorial](https://www.minidsp.com/applications/acoustic-measurements/psychoacoustic-measurements-with-mosqito)
- Daniel & Weber (1997): "Psychoacoustical Roughness: Implementation of an Optimized Model", Acta Acustica

---

*Research completed: 2026-01-08*
*Updated: 2026-01-09 - Confirmed fluctuation strength not in MoSQITo, added Soundscapy, updated library versions*
*Updated: 2026-01-09 - Added temporal evolution analysis section (beat/tempo, pitch tracking, feature evolution, segmentation)*
*Updated: 2026-01-09 - Resolved open questions (sample rate, stereo handling, thresholds, evolution features)*
