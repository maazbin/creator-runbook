"""Render a generic installed narrator with no service credentials."""

import os
from pathlib import Path
import shutil
import subprocess
import sys


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
    if sys.platform == "win32" and shutil.which("powershell.exe"):
        env = dict(os.environ, CREATOR_WAV=str(path), CREATOR_VOICE=voice)
        # Keep the source text and voice name outside executable PowerShell code.
        script = """
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    if ($env:CREATOR_VOICE) { $speaker.SelectVoice($env:CREATOR_VOICE) }
    $speaker.SetOutputToWaveFile($env:CREATOR_WAV)
    $speaker.Speak([Console]::In.ReadToEnd())
} finally { $speaker.Dispose() }
"""
        run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], text, env)
        return
    if sys.platform == "darwin" and shutil.which("say"):
        intermediate = path.with_suffix(".aiff")
        run(["say", "-o", str(intermediate), *(["-v", voice] if voice else [])], text)
        run(
            [
                ffmpeg,
                "-nostdin",
                "-loglevel",
                "error",
                "-i",
                str(intermediate),
                "-c:a",
                "pcm_s16le",
                str(path),
            ]
        )
        return
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        run([espeak, "-w", str(path), *(["-v", voice] if voice else []), "--stdin"], text)
        return
    raise ValueError(
        "Voiced episode needs an installed speech voice, supplied audio, or CREATOR_TTS_COMMAND"
    )
