from __future__ import annotations
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from .base import TTSDriver


class GTTSDriver(TTSDriver):
    def synthesize_to_wav(self, text: str, out_path: Path, target_ms: int) -> None:
        # Generate temp mp3 via gTTS (Hebrew); gTTS auto-detects language by token but we'll force 'he'
        tts = gTTS(text=text, lang="he")
        tmp_mp3 = out_path.with_suffix(".mp3")
        tts.save(str(tmp_mp3))

        # Convert to WAV 16k mono and pad/trim to ~target duration
        seg = AudioSegment.from_file(tmp_mp3)
        seg = seg.set_frame_rate(16000).set_channels(1)

        cur_ms = len(seg)
        if cur_ms < target_ms:
            seg = seg + AudioSegment.silent(duration=target_ms - cur_ms)
        elif cur_ms > target_ms * 1.05:  # allow ~5% slack before trimming
            seg = seg[:target_ms]

        seg.export(out_path, format="wav")
        try:
            tmp_mp3.unlink()
        except Exception:
            pass
