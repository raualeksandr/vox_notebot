from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Transcription
from app.services.openai_client import get_openai_client
from app.services.plans import get_transcription_model_for_plan


async def transcribe_audio(
    file_path: str,
    *,
    plan_key: str = "free",
    profile_type: str | None = None,
    model: str | None = None,
) -> str:
    """Transcribe an audio file with the configured OpenAI audio model."""
    transcription_model = model or get_transcription_model_for_plan(
        plan_key,
        profile_type,
    )
    client = get_openai_client()
    with open(file_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model=transcription_model,
            file=audio_file,
        )

    transcript_text = (response.text or "").strip()
    if not transcript_text:
        raise RuntimeError("OpenAI returned an empty transcription.")
    return transcript_text


async def get_recent_transcriptions(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 10,
) -> list[Transcription]:
    result = await session.execute(
        select(Transcription)
        .where(
            Transcription.user_id == user_id,
            Transcription.status == "completed",
            Transcription.transcript_text.is_not(None),
        )
        .order_by(Transcription.created_at.desc(), Transcription.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_user_transcription(
    session: AsyncSession,
    transcription_id: int,
    user_id: int,
) -> Transcription | None:
    result = await session.execute(
        select(Transcription).where(
            Transcription.id == transcription_id,
            Transcription.user_id == user_id,
            Transcription.status == "completed",
            Transcription.transcript_text.is_not(None),
        )
    )
    return result.scalar_one_or_none()
