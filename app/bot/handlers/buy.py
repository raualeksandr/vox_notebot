from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.keyboards.user import packages_keyboard


router = Router(name="buy")


@router.message(Command("buy"))
async def buy_command(message: Message) -> None:
    await message.answer(
        "Выберите пакет минут. Оплата будет подключена позже.",
        reply_markup=packages_keyboard(),
    )

