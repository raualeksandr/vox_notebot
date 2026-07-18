from contextlib import suppress
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import user_menu_keyboard
from app.bot.legal import CONSENT_TEXT, consent_keyboard, privacy_text
from app.config import get_settings
from app.services.billing import get_or_create_balance
from app.services.plans import is_plan_expired
from app.services.users import get_or_create_user, get_user_by_telegram_id


router = Router(name="start")


def _welcome_text(support_contact: str) -> str:
    return (
        "VoxNoteBot помогает превращать голосовые заметки и аудиофайлы "
        "в структурированный текст.\n\n"
        "Основной сценарий Premium HR — помощь оценщикам: HR-саммари, "
        "факты и интерпретации, люди, компетенции, зоны роста, рекомендации "
        "и черновик HR-отчёта.\n\n"
        "Также есть Personal-режим для личных заметок: очистка текста, саммари, "
        "задачи, рефлексия и план действий.\n\n"
        "Можно отправить Telegram voice note или аудиофайл mp3, m4a, wav, ogg.\n\n"
        "Тарифы:\n"
        "Free — 0 ₽, 30 минут, fast-транскрибация, Очистить и Саммари.\n"
        "Personal — 199 ₽, 300 минут, личные заметки.\n"
        "Premium HR — 1290 ₽, 1000 минут, premium-транскрибация и HR-функции.\n\n"
        "Тарифы и оплата: /buy\n"
        f"Вопросы доступа, оплаты и trial: {support_contact}"
    )


def _help_text(support_contact: str) -> str:
    return (
        "Команды:\n"
        "/start — описание продукта и тарифов\n"
        "/help — помощь и список команд\n"
        "/balance — тариф, минуты и срок доступа\n"
        "/history — последние транскрипции\n"
        "/buy — тарифы и инструкция оплаты\n"
        "/privacy — политика конфиденциальности\n"
        "/admin — меню администратора, только для админов\n\n"
        "Что можно отправлять:\n"
        "- Telegram voice note\n"
        "- аудиофайлы mp3, m4a, wav, ogg\n\n"
        "Доступ к функциям зависит от тарифа. Free даёт базовые действия, "
        "Personal открывает личные заметки, Premium HR открывает HR-функции "
        "для оценщиков.\n\n"
        "Ваш Telegram ID отображается в /start, /buy и /balance. "
        "Он нужен для ручной выдачи тарифа после оплаты.\n\n"
        f"Поддержка по оплате, trial и доступу: {support_contact}"
    )


async def _send_welcome(message: Message, settings, user, telegram_user) -> None:
    await message.answer(_welcome_text(settings.support_contact_username))
    await message.answer(f"Ваш Telegram ID: {telegram_user.id}")
    if is_plan_expired(user):
        await message.answer(
            "Ваш тариф истёк, доступен Free-режим. "
            f"Откройте /buy для продления или напишите "
            f"{settings.support_contact_username}."
        )
    await message.answer(
        "Используйте кнопки меню ниже.",
        reply_markup=user_menu_keyboard(is_admin=settings.is_admin(telegram_user.id)),
    )


@router.message(CommandStart())
async def start_command(message: Message, session: AsyncSession) -> None:
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
    await get_or_create_balance(session, user.id)

    if user.consent_accepted_at is None:
        await message.answer(CONSENT_TEXT, reply_markup=consent_keyboard())
        return

    await _send_welcome(message, settings, user, telegram_user)


@router.callback_query(F.data == "consent:accept")
async def consent_accept(callback: CallbackQuery, session: AsyncSession) -> None:
    settings = get_settings()
    user = await get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        language_code=callback.from_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    if user.consent_accepted_at is None:
        user.consent_accepted_at = datetime.now(timezone.utc)

    await callback.answer("Согласие принято.")
    with suppress(Exception):
        await callback.message.edit_reply_markup(reply_markup=None)
    await callback.bot.send_message(callback.from_user.id, "Спасибо! Готово ✅")
    await callback.bot.send_message(
        callback.from_user.id,
        _welcome_text(settings.support_contact_username),
    )
    await callback.bot.send_message(
        callback.from_user.id,
        "Используйте кнопки меню ниже.",
        reply_markup=user_menu_keyboard(
            is_admin=settings.is_admin(callback.from_user.id)
        ),
    )


@router.message(Command("privacy"))
async def privacy_command(message: Message) -> None:
    settings = get_settings()
    await message.answer(privacy_text(settings.support_contact_username))


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    settings = get_settings()
    await message.answer(_help_text(settings.support_contact_username))
    telegram_user = message.from_user
    await message.answer(
        "Меню команд:",
        reply_markup=user_menu_keyboard(
            is_admin=bool(
                telegram_user and settings.is_admin(telegram_user.id)
            )
        ),
    )
