from collections.abc import Collection

from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    normalized_username = username.strip().removeprefix("@").lower()
    if not normalized_username:
        return None

    result = await session.execute(
        select(User).where(User.username.ilike(normalized_username))
    )
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    language_code: str | None = None,
    admin_telegram_ids: Collection[int] = (),
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    role = "admin" if is_admin(telegram_id, admin_telegram_ids) else "user"

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
            role=role,
        )
        session.add(user)
    else:
        user.username = username
        user.first_name = first_name
        user.language_code = language_code
        user.role = role

    await session.flush()
    return user


def is_admin(telegram_id: int, admin_telegram_ids: Collection[int]) -> bool:
    return telegram_id in admin_telegram_ids


def display_name(user: TelegramUser) -> str:
    """Build a readable user name without database access."""
    return user.full_name or str(user.id)
