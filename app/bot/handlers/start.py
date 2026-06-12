from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message


router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(
        "Привет! Я бот для расшифровки голосовых заметок. "
        "Транскрибация будет подключена на следующем этапе."
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - показать помощь\n"
        "/balance - проверить баланс\n"
        "/buy - выбрать пакет минут\n"
        "/admin - открыть меню администратора"
    )

