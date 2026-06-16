import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import history_transcription_keyboard
from app.bot.message_utils import send_text_chunks
from app.config import get_settings
from app.services.transcription import (
    get_recent_transcriptions,
    get_user_transcription,
)
from app.services.users import get_or_create_user, get_user_by_telegram_id, get_user_profile


router = Router(name="history")


def _preview(text: str, limit: int = 80) -> str:
    compact_text = " ".join(text.split())
    if len(compact_text) <= limit:
        return compact_text
    return compact_text[: limit - 1].rstrip() + "…"


@router.message(Command("history"))
async def history_command(message: Message, session: AsyncSession) -> None:
    telegram_user = message.from_user
    if telegram_user is None:
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
    transcriptions = await get_recent_transcriptions(session, user.id, limit=10)
    if not transcriptions:
        await message.answer("У вас пока нет транскрипций.")
        return

    user_profile = await get_user_profile(session, user.id)
    include_hr_actions = (
        user_profile is not None and user_profile.profile_type == "hr_assessor"
    )
    include_pm_ba_actions = (
        user_profile is not None and user_profile.profile_type == "pm_ba"
    )
    await message.answer("Ваши последние транскрипции:")
    for transcription in transcriptions:
        duration_minutes = max(
            1,
            math.ceil(transcription.audio_duration_seconds / 60),
        )
        created_at = transcription.created_at.strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"{created_at}\n"
            f"Длительность: {duration_minutes} мин.\n"
            f"{_preview(transcription.transcript_text or '')}",
            reply_markup=history_transcription_keyboard(
                transcription.id,
                include_hr_actions=include_hr_actions,
                include_pm_ba_actions=include_pm_ba_actions,
            ),
        )


@router.callback_query(F.data.startswith("history:text:"))
async def show_transcription_text(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 3 or not callback_parts[2].isdigit():
        await callback.answer("Транскрипция не найдена.", show_alert=True)
        return

    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user is None:
        await callback.answer("Транскрипция не найдена.", show_alert=True)
        return

    transcription = await get_user_transcription(
        session,
        int(callback_parts[2]),
        user.id,
    )
    if transcription is None or not transcription.transcript_text:
        await callback.answer("Транскрипция не найдена.", show_alert=True)
        return

    await callback.answer()
    await send_text_chunks(
        callback.bot,
        callback.from_user.id,
        transcription.transcript_text,
    )
