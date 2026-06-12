from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router(name="balance")


@router.message(Command("balance"))
async def balance_command(message: Message) -> None:
    await message.answer("Баланс минут пока не подключён.")

