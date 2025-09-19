from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple

import typer
import pysubs2
from pydub import AudioSegment

# Local modules
from app.subs.normalize import normalize_srt
from app.tts.gtts import GTTSDriver
from app.audio.stitch import stitch_lines
from app.audio.mux import mux_audio_track

app = typer.Typer(help="JP→HE voice dubbing using existing Hebrew subtitles.")

BUILD_DIR = Path("build")
BUILD_DIR.mkdir(parents=True, exist_ok=True)


def _run(cmd: List[str]) -> None:
    """Run a shell command and raise on non‑zero."""
    typer.echo(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        typer.echo(res.stdout)
        typer.echo(res.stderr)
        raise typer.Exit(code=res.returncode)


@app.command("extract-subs")
def extract_subs(
    video: Path = typer.Option(..., exists=True, help="Input video (mp4/webm)."),
    track: int = typer.Option(0, help="Subtitle track index (0-based)."),
    out: Optional[Path] = typer.Option(None, "-o", help="Output SRT path."),
):
    """Extract embedded subtitle track to SRT using ffmpeg."""
    out = out or Path(BUILD_DIR / "subs.he.srt")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video),
        "-map", f"0:s:{track}",
        str(out)
    ]
    _run(cmd)
    typer.echo(f"✓ Extracted subtitles → {out}")


@app.command()
def dub(
    video: Path = typer.Option(..., exists=True, help="Input video path"),
    subs: Path = typer.Option(..., exists=True, help="Hebrew SRT (or ASS/VTT) path"),
    engine: str = typer.Option("gtts", help="TTS engine: gtts (default)"),
    voice: str = typer.Option("he-il", help="Engine-specific voice id (gTTS ignores)"),
    gap_ms: int = typer.Option(120, help="Silence gap between lines in ms"),
    replace_original: bool = typer.Option(False, help="Replace original audio instead of adding track"),
    keep_original: bool = typer.Option(True, help="Keep original JP audio as another track"),
):
    """Synthesize Hebrew voice from subtitles and mux into the video."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Normalize subtitles to SRT
    norm_srt = BUILD_DIR / "normalized.he.srt"
    normalize_srt(subs, norm_srt)
    typer.echo(f"✓ Normalized subs → {norm_srt}")

    # 2) Load subs
    ss = pysubs2.load(str(norm_srt), encoding="utf-8")

    # 3) Pick TTS driver
    if engine.lower() == "gtts":
        tts = GTTSDriver()
    else:
        typer.echo("Only gTTS is implemented in the scaffold.")
        raise typer.Exit(code=2)

    # 4) Synthesize per-line WAVs approx to cue durations
    line_wavs: List[Tuple[Path, int, int]] = []  # (wav_path, start_ms, end_ms)
    audio_dir = BUILD_DIR / "lines"
    audio_dir.mkdir(exist_ok=True)

    for i, ev in enumerate(ss):
        text = pysubs2.get_text(ev) or ev.text
        start_ms = int(ev.start)
        end_ms = int(ev.end)
        target_dur = max(300, end_ms - start_ms)  # minimum 300ms
        wav_path = audio_dir / f"line_{i:04d}.wav"
        tts.synthesize_to_wav(text=text, out_path=wav_path, target_ms=target_dur)
        line_wavs.append((wav_path, start_ms, end_ms))

    typer.echo(f"✓ Synthesized {len(line_wavs)} lines")

    # 5) Stitch into single narration track
    stitched_wav = BUILD_DIR / "he_voice.wav"
    stitched_aac = BUILD_DIR / "he_voice.aac"
    stitch_lines(line_wavs, stitched_wav, gap_ms=gap_ms)
    typer.echo(f"✓ Stitched → {stitched_wav}")

    # Encode AAC for muxing (pydub could do this, but ffmpeg is faster/predictable)
    _run(["ffmpeg", "-y", "-i", str(stitched_wav), "-c:a", "aac", "-b:a", "128k", str(stitched_aac)])
    typer.echo(f"✓ Encoded AAC → {stitched_aac}")

    # 6) Mux into the video
    out_mp4 = BUILD_DIR / "output.he.mp4"
    mux_audio_track(
        video=video,
        he_aac=stitched_aac,
        out_mp4=out_mp4,
        keep_original=keep_original and not replace_original,
    )
    typer.echo(f"🎉 Done → {out_mp4}")


if __name__ == "__main__":
    app()
