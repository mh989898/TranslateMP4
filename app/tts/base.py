from __future__ import annotations
from pathlib import Path
from abc import ABC, abstractmethod


class TTSDriver(ABC):
    @abstractmethod
    def synthesize_to_wav(self, text: str, out_path: Path, target_ms: int) -> None:
        ...
