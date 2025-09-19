from __future__ import annotations
from pathlib import Path
import subprocess


def _run(cmd):
    subprocess.check_call(cmd)


def mux_audio_track(video: Path, he_aac: Path, out_mp4: Path, keep_original: bool = True) -> None:
    """Mux Hebrew AAC into video. If keep_original is True, add as extra track; else replace."""
    if keep_original:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(he_aac),
            "-map", "0:v:0", "-map", "0:a:0?", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac",
            "-metadata:s:a:1", "language=heb",
            str(out_mp4),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(he_aac),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac",
            "-metadata:s:a:0", "language=heb",
            str(out_mp4),
        ]
    _run(cmd)
