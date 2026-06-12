import logging
import math
import tempfile
from collections.abc import Awaitable, Callable
from contextlib import suppress
from decimal import Decimal
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import transcription_actions_keyboard
from app.config import get_settings
from app.db.models import Transcription
from app.services.billing import (
    create_balance_transaction,
    get_or_create_balance,
    remove_minutes,
)
from app.services.openai_client import OpenAIKeyNotConfiguredError
from app.services.text_processing import clean_text, extract_tasks, summarize_text
from app.services.transcription import transcribe_audio
from app.services.users import get_or_create_user, get_user_by_telegram_id


logger = logging.getLogger(__name__)
router = Router(name="voice")
TELEGRAM_MESSAGE_CHUNK_SIZE = 4000

TextProcessor = Callable[[str], Awaitable[str]]


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


async def _send_text_chunks(message: Message, text: str) -> None:
    for chunk in _split_text(text):
        await message.answer(chunk)


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
        await _send_text_chunks(message, transcript_text)
        await message.answer(
            "Что сделать с транскрипцией?",
            reply_markup=transcription_actions_keyboard(transcription.id),
        )
    finally:
        if temporary_path is not None:
            with suppress(OSError):
                temporary_path.unlink(missing_ok=True)


@router.callback_query(F.data.startswith("text:"))
async def process_transcription_text(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 3 or not callback_parts[2].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[1]
    transcription_id = int(callback_parts[2])
    transcription = await session.get(Transcription, transcription_id)
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if (
        transcription is None
        or user is None
        or transcription.user_id != user.id
        or transcription.status != "completed"
        or not transcription.transcript_text
    ):
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    processors: dict[str, tuple[str, TextProcessor]] = {
        "clean": ("🧹 Очищенный текст:", clean_text),
        "summary": ("📝 Summary:", summarize_text),
        "tasks": ("✅ Задачи:", extract_tasks),
    }
    processor_config = processors.get(action)
    if processor_config is None:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    title, processor = processor_config
    try:
        result = await processor(transcription.transcript_text)
    except (OpenAIKeyNotConfiguredError, OpenAIError, ValueError, RuntimeError):
        logger.exception("Text processing failed for transcription %s", transcription.id)
        await callback.bot.send_message(
            callback.from_user.id,
            "Обработка текста временно недоступна.",
        )
        return

    await callback.bot.send_message(callback.from_user.id, title)
    for chunk in _split_text(result):
        await callback.bot.send_message(callback.from_user.id, chunk)
