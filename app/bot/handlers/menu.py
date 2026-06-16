from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.admin import admin_command
from app.bot.handlers.balance import balance_command
from app.bot.handlers.buy import buy_command
from app.bot.handlers.history import history_command
from app.bot.handlers.onboarding import setup_command
from app.bot.handlers.start import help_command


router = Router(name="menu")


@router.message(F.text == "🎙 Отправить голосовое")
async def voice_hint(message: Message) -> None:
    await message.answer(
        "Нажмите на микрофон в Telegram и отправьте голосовое сообщение. "
        "Я превращу его в текст."
    )


@router.message(F.text == "📚 История")
async def history_button(message: Message, session: AsyncSession) -> None:
    await history_command(message, session)


@router.message(F.text == "💰 Баланс")
async def balance_button(message: Message, session: AsyncSession) -> None:
    await balance_command(message, session)


@router.message(F.text == "🛒 Купить минуты")
async def buy_button(message: Message) -> None:
    await buy_command(message)


@router.message(F.text == "⚙️ Настройка")
async def setup_button(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await setup_command(message, session, state)


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message) -> None:
    await help_command(message)


@router.message(F.text == "⚙️ Админка")
async def admin_button(message: Message, session: AsyncSession) -> None:
    await admin_command(message, session)
