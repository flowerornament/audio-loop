"""NRT (Non-Real-Time) wrapper for simple function syntax."""

from pathlib import Path

# Template for wrapping a simple function in NRT boilerplate
NRT_WRAPPER_TEMPLATE = '''// Auto-generated NRT wrapper by audioloop
(
var userFunc = __USER_CODE__;
var duration = __DURATION__;
var outputPath = "__OUTPUT_PATH__";

SynthDef(\\audioloop_render, { |out=0|
    Out.ar(out, userFunc.value);
}).store;

var score = Score([
    [0.0, [\\s_new, \\audioloop_render, 1000, 0, 0]],
    [duration, [\\n_free, 1000]],
]);

score.recordNRT(
    outputFilePath: outputPath,
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: duration,
    action: { "Render complete".postln; 0.exit; }
);
)
'''


def needs_wrapping(code: str) -> bool:
    """Check if code needs NRT wrapping.

    Returns True if the code is a simple function that needs to be
    wrapped in NRT boilerplate. Returns False if the code already
    contains recordNRT (full NRT mode).

    Args:
        code: SuperCollider source code.

    Returns:
        True if wrapping is needed, False otherwise.
    """
    return "recordNRT" not in code


def wrap_function(code: str, duration: float, output_path: Path) -> str:
    """Wrap a simple function in NRT boilerplate.

    Takes a SuperCollider function like `{ SinOsc.ar(440) }` and wraps it
    in a complete NRT rendering script.

    Args:
        code: A SuperCollider function expression (e.g., `{ SinOsc.ar(440) }`).
        duration: Duration in seconds to render.
        output_path: Path where the WAV file will be written.

    Returns:
        Complete SuperCollider script ready for NRT rendering.
    """
    return (
        NRT_WRAPPER_TEMPLATE
        .replace("__USER_CODE__", code.strip())
        .replace("__DURATION__", str(duration))
        .replace("__OUTPUT_PATH__", str(output_path))
    )


def replace_placeholders(
    code: str,
    output_path: Path,
    duration: float | None = None,
) -> str:
    """Replace placeholders in SuperCollider code.

    For full NRT mode code, replaces:
    - __OUTPUT_PATH__ with the actual output path

    For wrapped mode (if duration provided), also replaces:
    - __DURATION__ with the duration value
    - __USER_CODE__ with user's function (handled by wrap_function)

    Args:
        code: SuperCollider source code with placeholders.
        output_path: Path where the WAV file will be written.
        duration: Optional duration in seconds (for wrapped mode).

    Returns:
        Code with placeholders replaced.
    """
    result = code.replace("__OUTPUT_PATH__", str(output_path))

    if duration is not None:
        result = result.replace("__DURATION__", str(duration))

    return result
