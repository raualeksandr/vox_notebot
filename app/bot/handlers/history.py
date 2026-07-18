import math
from contextlib import suppress

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import history_transcription_keyboard
from app.bot.message_utils import send_text_chunks
from app.bot.role_actions import (
    get_visible_universal_callback_keys,
    role_action_keyboard_flags,
)
from app.config import get_settings
from app.services.plans import get_effective_plan
from app.services.transcription import (
    delete_user_transcription,
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
    profile_type = user_profile.profile_type if user_profile is not None else None
    plan_key = get_effective_plan(user)
    role_keyboard_flags = role_action_keyboard_flags(
        profile_type,
        plan_key,
    )
    visible_universal_callback_keys = get_visible_universal_callback_keys(
        profile_type,
        plan_key,
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
                visible_universal_callback_keys=visible_universal_callback_keys,
                **role_keyboard_flags,
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


@router.callback_query(F.data.startswith("txn_del:"))
async def delete_transcription_callback(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer("Запись не найдена.")
        return

    transcription_id = int(parts[1])
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user is None:
        await callback.answer("Запись не найдена.")
        return

    deleted = await delete_user_transcription(session, transcription_id, user.id)
    if not deleted:
        await callback.answer("Запись не найдена.")
        return

    await callback.answer("Запись удалена.")
    with suppress(TelegramAPIError):
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.bot.send_message(
        callback.from_user.id,
        "🗑 Транскрипция удалена.",
    )
