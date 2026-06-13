from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import user_menu_keyboard
from app.config import get_settings
from app.services.billing import get_or_create_balance
from app.services.users import get_or_create_user


router = Router(name="start")


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

    await message.answer(
        f"Привет, {telegram_user.first_name}! Я бот для голосовых заметок.\n\n"
        "Отправьте voice-сообщение, и позже я смогу транскрибировать его в текст. "
        "На текущем этапе транскрибация работает как заглушка.\n\n"
        "Используйте /balance для проверки минут и /buy для выбора пакета."
    )
    await message.answer(
        "Используйте кнопки меню ниже.",
        reply_markup=user_menu_keyboard(is_admin=settings.is_admin(telegram_user.id)),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/balance - показать баланс минут и последние операции\n"
        "/buy - выбрать пакет минут\n"
        "/history - открыть последние транскрипции\n"
        "/admin - меню администратора, доступное только администраторам\n\n"
        "После транскрибации можно очистить текст, получить Summary "
        "или выделить задачи."
    )
    telegram_user = message.from_user
    await message.answer(
        "Меню команд:",
        reply_markup=user_menu_keyboard(
            is_admin=bool(
                telegram_user and get_settings().is_admin(telegram_user.id)
            )
        ),
    )
