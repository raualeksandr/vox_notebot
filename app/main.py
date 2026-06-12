import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.router import router
from app.bot.middlewares.database import DatabaseSessionMiddleware
from app.config import get_settings
from app.db.session import create_session_factory
from app.services.openai_client import close_openai_client


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Fill it in the local .env file.")

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.update.middleware(
        DatabaseSessionMiddleware(create_session_factory(settings))
    )
    dispatcher.include_router(router)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await close_openai_client()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
