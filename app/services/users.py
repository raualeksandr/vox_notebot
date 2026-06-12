from aiogram.types import User as TelegramUser


def display_name(user: TelegramUser) -> str:
    """Build a readable user name without database access."""
    return user.full_name or str(user.id)

