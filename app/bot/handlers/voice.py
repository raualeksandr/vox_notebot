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
from app.bot.message_utils import answer_text_chunks, send_text_chunks
from app.bot.role_actions import (
    ROLE_ACTIONS_BY_CALLBACK_KEY,
    can_use_role_callback,
    can_use_universal_callback,
    get_visible_universal_callback_keys,
    role_action_denial_message,
    role_action_keyboard_flags,
)
from app.config import get_settings
from app.db.models import Transcription
from app.services.billing import (
    create_balance_transaction,
    get_or_create_balance,
    remove_minutes,
)
from app.services.openai_client import OpenAIKeyNotConfiguredError
from app.services.plans import (
    get_text_model_for_plan,
    get_transcription_model_for_plan,
)
from app.services.text_processing import (
    clean_text,
    extract_key_points,
    extract_questions,
    extract_tasks,
    suggest_next_steps,
    summarize_text,
    text_model_override,
)
from app.services.transcription import get_user_transcription, transcribe_audio
from app.services.users import get_or_create_user, get_user_by_telegram_id, get_user_profile


logger = logging.getLogger(__name__)
router = Router(name="voice")

TextProcessor = Callable[[str], Awaitable[str]]
TEXT_PROCESSORS: dict[str, tuple[str | None, TextProcessor]] = {
    "clean": ("🧹 Очищенный текст:", clean_text),
    "summary": ("📝 Саммари:", summarize_text),
    "tasks": ("✅ Задачи:", extract_tasks),
    "key_points": (None, extract_key_points),
    "questions": (None, extract_questions),
    "next_steps": (None, suggest_next_steps),
}


def _universal_callback_key(action: str) -> str:
    if action in {"clean", "summary", "tasks"}:
        return f"text:{action}"
    return action


def _format_minutes(value: Decimal) -> str:
    return f"{value.normalize():f}"


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
        user_profile = await get_user_profile(session, user.id)
        profile_type = user_profile.profile_type if user_profile is not None else None
        transcription_model = get_transcription_model_for_plan(
            user.current_plan or "free",
            profile_type,
        )

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
            model=transcription_model,
            status="pending",
            cost_estimate=Decimal("0"),
        )
        session.add(transcription)
        await session.flush()

        try:
            transcript_text = await transcribe_audio(
                str(temporary_path),
                model=transcription_model,
            )
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
        await answer_text_chunks(message, transcript_text)
        role_keyboard_flags = role_action_keyboard_flags(
            profile_type,
            user.current_plan,
        )
        visible_universal_callback_keys = get_visible_universal_callback_keys(
            profile_type,
            user.current_plan,
        )
        await message.answer(
            "Что сделать с транскрипцией?",
            reply_markup=transcription_actions_keyboard(
                transcription.id,
                visible_universal_callback_keys=visible_universal_callback_keys,
                **role_keyboard_flags,
            ),
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
    await _process_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("key_points:")
    | F.data.startswith("questions:")
    | F.data.startswith("next_steps:")
)
async def process_universal_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("hr_summary:")
    | F.data.startswith("competency_notes:")
    | F.data.startswith("evidence:")
    | F.data.startswith("people:")
    | F.data.startswith("strengths_growth:")
    | F.data.startswith("development_recommendations:")
    | F.data.startswith("hr_report:")
)
async def process_hr_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_role_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("meeting_notes:")
    | F.data.startswith("user_story:")
    | F.data.startswith("acceptance_criteria:")
    | F.data.startswith("risks_assumptions:")
)
async def process_pm_ba_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_role_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("idea_brief:")
    | F.data.startswith("business_hypotheses:")
    | F.data.startswith("mvp_scope:")
    | F.data.startswith("pitch_summary:")
)
async def process_founder_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_role_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("study_notes:")
    | F.data.startswith("research_summary:")
    | F.data.startswith("explain_simply:")
    | F.data.startswith("flashcards:")
)
async def process_student_researcher_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_role_transcription_action(callback, session, action, transcription_id)


@router.callback_query(
    F.data.startswith("reflection:")
    | F.data.startswith("categorize_note:")
    | F.data.startswith("tags:")
    | F.data.startswith("action_plan:")
)
async def process_personal_notes_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Обрабатываю...")

    callback_parts = (callback.data or "").split(":")
    if len(callback_parts) != 2 or not callback_parts[1].isdigit():
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    action = callback_parts[0]
    transcription_id = int(callback_parts[1])
    await _process_role_transcription_action(callback, session, action, transcription_id)


async def _process_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
    action: str,
    transcription_id: int,
) -> None:
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user is None:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    transcription = await get_user_transcription(
        session,
        transcription_id,
        user.id,
    )
    if transcription is None or not transcription.transcript_text:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    processor_config = TEXT_PROCESSORS.get(action)
    if processor_config is None:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    title, processor = processor_config
    user_profile = await get_user_profile(session, user.id)
    profile_type = user_profile.profile_type if user_profile is not None else None
    plan_key = user.current_plan or "free"
    if not can_use_universal_callback(
        _universal_callback_key(action),
        profile_type,
        plan_key,
    ):
        await callback.bot.send_message(
            callback.from_user.id,
            "Эта функция недоступна на вашем тарифе.",
        )
        return

    text_model = get_text_model_for_plan(plan_key, profile_type)
    try:
        with text_model_override(text_model):
            result = await processor(transcription.transcript_text)
    except (OpenAIKeyNotConfiguredError, OpenAIError, ValueError, RuntimeError):
        logger.exception("Text processing failed for transcription %s", transcription.id)
        await callback.bot.send_message(
            callback.from_user.id,
            "Обработка текста временно недоступна.",
        )
        return

    if title:
        await callback.bot.send_message(callback.from_user.id, title)
    await send_text_chunks(callback.bot, callback.from_user.id, result)


async def _process_role_transcription_action(
    callback: CallbackQuery,
    session: AsyncSession,
    action: str,
    transcription_id: int,
) -> None:
    role_action_config = ROLE_ACTIONS_BY_CALLBACK_KEY.get(action)
    if role_action_config is None:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    expected_profile_type, role_action = role_action_config
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if user is None:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    transcription = await get_user_transcription(
        session,
        transcription_id,
        user.id,
    )
    if transcription is None or not transcription.transcript_text:
        await callback.bot.send_message(callback.from_user.id, "Транскрипция не найдена.")
        return

    user_profile = await get_user_profile(session, user.id)
    if user_profile is None or user_profile.profile_type != expected_profile_type:
        await callback.bot.send_message(
            callback.from_user.id,
            "Эта функция недоступна для вашего профиля.",
        )
        return

    plan_key = user.current_plan or "free"
    if not can_use_role_callback(action, user_profile.profile_type, plan_key):
        await callback.bot.send_message(
            callback.from_user.id,
            role_action_denial_message(expected_profile_type),
        )
        return

    text_model = get_text_model_for_plan(
        plan_key,
        user_profile.profile_type,
    )
    try:
        with text_model_override(text_model):
            result = await role_action.processor(transcription.transcript_text)
    except (OpenAIKeyNotConfiguredError, OpenAIError, ValueError, RuntimeError):
        logger.exception(
            "Role-specific text processing failed for transcription %s",
            transcription.id,
        )
        await callback.bot.send_message(
            callback.from_user.id,
            "Обработка текста временно недоступна.",
        )
        return

    await send_text_chunks(callback.bot, callback.from_user.id, result)
