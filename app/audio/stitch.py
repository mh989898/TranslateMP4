from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from pydub import AudioSegment


def stitch_lines(line_wavs: List[Tuple[Path, int, int]], out_wav: Path, gap_ms: int = 120) -> None:
    """Concatenate line WAVs in order, insert small gaps, add tiny fades."""
    acc = AudioSegment.silent(duration=0)
    for wav_path, _start, _end in line_wavs:
        seg = AudioSegment.from_wav(wav_path)
        seg = seg.fade_in(5).fade_out(5)
        acc += seg + AudioSegment.silent(duration=gap_ms)
    acc.export(out_wav, format="wav")
