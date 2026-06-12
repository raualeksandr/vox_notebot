from aiogram import F, Router
from aiogram.types import Message


router = Router(name="voice")


@router.message(F.voice)
async def voice_message(message: Message) -> None:
    await message.answer(
        "Транскрибация пока не подключена. "
        "На следующем этапе здесь будет текст."
    )

