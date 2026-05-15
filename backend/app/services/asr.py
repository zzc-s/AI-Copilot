"""语音转写（可插拔 ASR）。"""
from __future__ import annotations

from app.core.config import settings
from app.services.providers import get_asr_provider


def transcribe_audio(audio_bytes: bytes, mime_type: str) -> dict:
    prov = get_asr_provider()
    return prov.transcribe(audio_bytes, mime_type, settings.asr_model)
