import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Transcription

logger = logging.getLogger(__name__)


async def purge_expired_transcriptions(
    session: AsyncSession,
    retention_days: int,
) -> int:
    """Удаляет транскрипции старше retention_days. Возвращает число удалённых."""
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await session.execute(
        delete(Transcription).where(Transcription.created_at < cutoff)
    )
    return result.rowcount or 0
