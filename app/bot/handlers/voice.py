from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.billing import get_or_create_balance
from app.services.users import get_or_create_user


router = Router(name="voice")


@router.message(F.voice)
async def voice_message(message: Message, session: AsyncSession) -> None:
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
    if user.is_blocked:
        await message.answer("Ваш аккаунт заблокирован.")
        return

    balance = await get_or_create_balance(session, user.id)
    if balance.minutes_remaining <= 0:
        await message.answer(
            "На балансе нет доступных минут. Пополните баланс через /buy."
        )
        return

    await message.answer(
        "Транскрибация пока не подключена. "
        "На следующем этапе здесь будет текст."
    )
