"""Run a host-configured speech command. The OS narrator is not a performance."""

from pathlib import Path
import subprocess


def run(argv, text="", env=None):
    result = subprocess.run(
        argv,
        input=text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
        env=env,
    )
    if result.returncode:
        raise ValueError("Installed speech engine failed: " + result.stderr.strip()[-480:])


def record(path: Path, text: str, voice: str, ffmpeg: str):
    raise ValueError(
        "The operating-system narrator has no performance. "
        "Render the take as in references/voice.md and supply it as the scene audio, "
        "or set CREATOR_TTS_COMMAND to that engine."
    )
