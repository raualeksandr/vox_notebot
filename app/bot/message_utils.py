from aiogram import Bot
from aiogram.types import Message


TELEGRAM_MESSAGE_CHUNK_SIZE = 4000


def split_text(
    text: str,
    chunk_size: int = TELEGRAM_MESSAGE_CHUNK_SIZE,
) -> list[str]:
    chunks: list[str] = []
    remaining = text.strip()

    while len(remaining) > chunk_size:
        split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = remaining.rfind(" ", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = chunk_size

        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


async def answer_text_chunks(message: Message, text: str) -> None:
    for chunk in split_text(text):
        await message.answer(chunk)


async def send_text_chunks(bot: Bot, chat_id: int, text: str) -> None:
    for chunk in split_text(text):
        await bot.send_message(chat_id, chunk)
