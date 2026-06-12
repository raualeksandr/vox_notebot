import logging
import math
import tempfile
from contextlib import suppress
from decimal import Decimal
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Transcription
from app.services.billing import (
    create_balance_transaction,
    get_or_create_balance,
    remove_minutes,
)
from app.services.transcription import (
    OpenAIKeyNotConfiguredError,
    transcribe_audio,
)
from app.services.users import get_or_create_user


logger = logging.getLogger(__name__)
router = Router(name="voice")
TELEGRAM_MESSAGE_CHUNK_SIZE = 4000


def _format_minutes(value: Decimal) -> str:
    return f"{value.normalize():f}"


def _split_text(text: str, chunk_size: int = TELEGRAM_MESSAGE_CHUNK_SIZE) -> list[str]:
    chunks: list[str] = []
    remaining = text.strip()

    while len(remaining) > chunk_size:
        split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = remaining.rfind(" ", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = chunk_size

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


@router.message(F.voice)
async def voice_message(message: Message, session: AsyncSession) -> None:
    telegram_user = message.from_user
    voice = message.voice
    if telegram_user is None or voice is None:
        return

    settings = get_settings()
    user = await get_or_create_user(
        session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    if user.is_blocked:
        await message.answer("Ваш аккаунт заблокирован.")
        return

    duration_seconds = max(0, voice.duration)
    required_minutes = max(1, math.ceil(duration_seconds / 60))
    balance = await get_or_create_balance(session, user.id)
    if balance.minutes_remaining < required_minutes:
        await message.answer(
            "Недостаточно минут. "
            f"Баланс: {_format_minutes(balance.minutes_remaining)} мин, "
            f"голосовое: {required_minutes} мин. Пополните баланс через /buy."
        )
        return

    if not settings.openai_api_key.strip():
        await message.answer(
            "OpenAI API key не настроен. Транскрибация временно недоступна."
        )
        return

    await message.answer("Принял голосовое, транскрибирую...")

    temporary_path: Path | None = None
    transcription: Transcription | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_file:
            temporary_path = Path(temp_file.name)

        try:
            await message.bot.download(voice, destination=temporary_path)
        except (TelegramAPIError, OSError):
            logger.exception("Failed to download Telegram voice file")
            await message.answer(
                "Не удалось скачать голосовое сообщение. "
                "Минуты не списаны. Попробуйте позже."
            )
            return

        transcription = Transcription(
            user_id=user.id,
            audio_duration_seconds=duration_seconds,
            transcript_text=None,
            model=settings.transcription_model,
            status="pending",
            cost_estimate=Decimal("0"),
        )
        session.add(transcription)
        await session.flush()

        try:
            transcript_text = await transcribe_audio(str(temporary_path))
        except OpenAIKeyNotConfiguredError:
            transcription.status = "failed"
            await session.flush()
            await message.answer(
                "OpenAI API key не настроен. Транскрибация временно недоступна."
            )
            return
        except (OpenAIError, OSError, RuntimeError):
            logger.exception("OpenAI transcription failed")
            transcription.status = "failed"
            await session.flush()
            await message.answer(
                "Не удалось транскрибировать аудио. "
                "Минуты не списаны. Попробуйте позже."
            )
            return

        try:
            balance = await remove_minutes(session, user.id, required_minutes)
        except ValueError:
            transcription.status = "failed"
            await session.flush()
            await message.answer(
                "Недостаточно минут для завершения операции. "
                "Минуты не списаны. Пополните баланс через /buy."
            )
            return

        transcription.transcript_text = transcript_text
        transcription.status = "completed"
        await create_balance_transaction(
            session,
            user_id=user.id,
            transaction_type="usage",
            minutes_delta=-required_minutes,
            reason=f"Транскрибация #{transcription.id}",
        )
        await session.flush()

        await message.answer(
            f"Готово. Списано {required_minutes} мин. "
            f"Остаток: {_format_minutes(balance.minutes_remaining)} мин."
        )
        for chunk in _split_text(transcript_text):
            await message.answer(chunk)
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)
