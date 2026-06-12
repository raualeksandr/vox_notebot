from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards.admin import admin_menu_keyboard
from app.config import get_settings


router = Router(name="admin")


@router.message(Command("admin"))
async def admin_command(message: Message) -> None:
    user = message.from_user
    if user is None or not get_settings().is_admin(user.id):
        await message.answer("Команда доступна только администраторам.")
        return

    await message.answer(
        "Панель администратора. Бизнес-логика будет добавлена позже.",
        reply_markup=admin_menu_keyboard(),
    )

