from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import user_menu_keyboard
from app.config import get_settings
from app.services.billing import get_or_create_balance
from app.services.users import get_or_create_user


router = Router(name="start")


WELCOME_TEXT = (
    "VoxNoteBot превращает голосовые заметки в аккуратный текст, саммари и "
    "рабочие материалы.\n\n"
    "Основные режимы:\n"
    "- Личные заметки: очистка, саммари, задачи, рефлексия, план.\n"
    "- HR / оценка персонала: HR-саммари, факты/интерпретации, люди, "
    "компетенции, сильные стороны/зоны роста, рекомендации и HR-отчёт.\n\n"
    "Тарифы:\n"
    "Free - 30 минут, fast-транскрибация, Очистить и Саммари.\n"
    "Personal - 199 RUB, 300 минут, личные заметки: Очистить, Саммари, "
    "Задачи, Рефлексия, План.\n"
    "Premium HR - 1290 RUB, 1000 минут, premium-транскрибация, HR-функции "
    "для оценщиков.\n\n"
    "Отправьте голосовое сообщение, чтобы начать."
)


HELP_TEXT = (
    "Команды:\n"
    "/start - описание продукта и тарифов\n"
    "/help - помощь и список команд\n"
    "/balance - баланс минут и последние операции\n"
    "/history - последние транскрипции\n"
    "/buy - тарифы / купить минуты\n"
    "/admin - меню администратора, только для админов\n\n"
    "Доступ к функциям зависит от тарифа. Free даёт базовые действия, "
    "Personal открывает личные заметки, Premium HR открывает HR-функции "
    "для оценщиков."
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

    await message.answer(WELCOME_TEXT)
    await message.answer(
        "Используйте кнопки меню ниже.",
        reply_markup=user_menu_keyboard(is_admin=settings.is_admin(telegram_user.id)),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)
    telegram_user = message.from_user
    await message.answer(
        "Меню команд:",
        reply_markup=user_menu_keyboard(
            is_admin=bool(
                telegram_user and get_settings().is_admin(telegram_user.id)
            )
        ),
    )
