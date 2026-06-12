from openai import AsyncOpenAI

from app.config import get_settings


class OpenAIKeyNotConfiguredError(RuntimeError):
    """Raised when transcription is requested without an API key."""


async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file with the configured OpenAI audio model."""
    settings = get_settings()
    api_key = settings.openai_api_key.strip()
    if not api_key:
        raise OpenAIKeyNotConfiguredError("OPENAI_API_KEY is not configured.")

    async with AsyncOpenAI(api_key=api_key) as client:
        with open(file_path, "rb") as audio_file:
            response = await client.audio.transcriptions.create(
                model=settings.transcription_model,
                file=audio_file,
            )

    transcript_text = (response.text or "").strip()
    if not transcript_text:
        raise RuntimeError("OpenAI returned an empty transcription.")
    return transcript_text
