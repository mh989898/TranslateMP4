from __future__ import annotations
from pathlib import Path
import pysubs2


def normalize_srt(in_path: Path, out_path: Path) -> None:
    """Load any common subtitle format, output clean SRT: sorted and de-overlapped."""
    subs = pysubs2.load(str(in_path), encoding="utf-8")
    # sort by start time
    subs.sort()

    # fix tiny overlaps by pushing next start forward 1–2 ms
    for prev, cur in zip(subs, subs[1:]):
        if cur.start < prev.end:
            cur.start = prev.end + 2
            if cur.end <= cur.start:
                cur.end = cur.start + 200  # ensure minimum duration

    subs.save(str(out_path), format_="srt")
