from openai import AsyncOpenAI

from app.config import get_settings


class OpenAIKeyNotConfiguredError(RuntimeError):
    """Raised when an OpenAI operation is requested without an API key."""


_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """Create the shared OpenAI client only when an API operation is requested."""
    global _client

    settings = get_settings()
    api_key = settings.openai_api_key.strip()
    if not api_key:
        raise OpenAIKeyNotConfiguredError("OPENAI_API_KEY is not configured.")

    if _client is None:
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def close_openai_client() -> None:
    global _client

    if _client is not None:
        await _client.close()
        _client = None
