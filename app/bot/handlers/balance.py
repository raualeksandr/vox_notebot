from decimal import Decimal

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.billing import (
    get_or_create_balance,
    get_recent_balance_transactions,
)
from app.services.plans import (
    get_effective_plan,
    get_plan_expiration_text,
    is_plan_expired,
)
from app.services.users import get_or_create_user


router = Router(name="balance")


def format_minutes(value: Decimal) -> str:
    return f"{value.normalize():f}"


@router.message(Command("balance"))
async def balance_command(message: Message, session: AsyncSession) -> None:
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
    balance = await get_or_create_balance(session, user.id)
    transactions = await get_recent_balance_transactions(session, user.id)
    raw_plan = user.current_plan or "free"
    effective_plan = get_effective_plan(user)

    lines = [
        f"Ваш Telegram ID: {telegram_user.id}",
        f"current_plan: {raw_plan}",
        f"plan_expires_at: {get_plan_expiration_text(user)}",
    ]
    if effective_plan != raw_plan:
        lines.append(f"effective_plan: {effective_plan}")
    if is_plan_expired(user):
        lines.append("Тариф истёк. Сейчас доступен Free-режим.")

    lines.extend(
        [
            f"Текущий баланс: {format_minutes(balance.minutes_remaining)} минут.",
            f"Всего начислено: {format_minutes(balance.minutes_total)} минут.",
            f"Использовано: {format_minutes(balance.minutes_used)} минут.",
        ]
    )

    if transactions:
        lines.append("\nПоследние операции:")
        for transaction in transactions:
            delta = Decimal(transaction.minutes_delta)
            sign = "+" if delta > 0 else ""
            lines.append(
                f"{sign}{format_minutes(delta)} мин. - "
                f"{transaction.reason or transaction.type}"
            )

    await message.answer("\n".join(lines))
