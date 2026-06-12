from pathlib import Path


async def transcribe_audio(audio_path: str | Path) -> str:
    """Return a placeholder until OpenAI transcription is connected."""
    _ = audio_path
    return "Тестовая транскрибация: сервис пока не подключён."

