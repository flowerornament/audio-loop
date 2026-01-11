"""Spectrogram generation for visual audio feedback.

Generates stacked waveform/spectrogram/chromagram visualizations
as PNG files for Claude to analyze alongside numeric features.
"""

from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np


def generate_spectrogram(
    audio_path: Path, output_path: Path, sr: int | None = None
) -> Path:
    """Generate a stacked visualization PNG with waveform, spectrogram, and chromagram.

    Creates a figure with three vertically stacked subplots sharing the x-axis:
    - Top: Waveform (amplitude over time)
    - Middle: Mel spectrogram (frequency content in dB)
    - Bottom: Chromagram (pitch class distribution)

    Args:
        audio_path: Path to input audio file (WAV).
        output_path: Path for output PNG file.
        sr: Sample rate to use. If None, uses native sample rate.

    Returns:
        Path to the generated PNG file.
    """
    # Load audio (mono for visualization)
    y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)

    # Create figure with 3 stacked subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # Top: Waveform
    librosa.display.waveshow(y, sr=sample_rate, ax=axes[0], color="#2196F3")
    axes[0].set_ylabel("Amplitude")
    axes[0].set_title("Waveform")

    # Middle: Mel spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sample_rate, n_mels=128)
    S_db = librosa.power_to_db(S, ref=np.max)
    img = librosa.display.specshow(
        S_db,
        sr=sample_rate,
        x_axis="time",
        y_axis="mel",
        ax=axes[1],
        cmap="magma",
    )
    axes[1].set_ylabel("Mel Frequency")
    axes[1].set_title("Mel Spectrogram")
    fig.colorbar(img, ax=axes[1], format="%+2.0f dB", pad=0.01)

    # Bottom: Chromagram
    chroma = librosa.feature.chroma_stft(y=y, sr=sample_rate)
    img_chroma = librosa.display.specshow(
        chroma,
        sr=sample_rate,
        x_axis="time",
        y_axis="chroma",
        ax=axes[2],
        cmap="coolwarm",
    )
    axes[2].set_ylabel("Pitch Class")
    axes[2].set_title("Chromagram")
    fig.colorbar(img_chroma, ax=axes[2], pad=0.01)

    # Only show x-axis label on bottom subplot
    for ax in axes[:-1]:
        ax.label_outer()

    axes[-1].set_xlabel("Time (s)")

    # Save with tight layout
    plt.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return output_path
