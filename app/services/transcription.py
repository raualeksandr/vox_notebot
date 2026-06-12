from app.config import get_settings
from app.services.openai_client import (
    OpenAIKeyNotConfiguredError,
    get_openai_client,
)


async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file with the configured OpenAI audio model."""
    settings = get_settings()
    client = get_openai_client()
    with open(file_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model=settings.transcription_model,
            file=audio_file,
        )

    transcript_text = (response.text or "").strip()
    if not transcript_text:
        raise RuntimeError("OpenAI returned an empty transcription.")
    return transcript_text
