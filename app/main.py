import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.router import router
from app.bot.middlewares.database import DatabaseSessionMiddleware
from app.config import get_settings
from app.db.session import create_session_factory
from app.services.openai_client import close_openai_client
from app.services.retention import purge_expired_transcriptions

logger = logging.getLogger(__name__)

RETENTION_INTERVAL_SECONDS = 24 * 60 * 60


async def _retention_loop(
    session_factory: async_sessionmaker[AsyncSession],
    retention_days: int,
) -> None:
    while True:
        try:
            async with session_factory() as session:
                deleted = await purge_expired_transcriptions(session, retention_days)
                await session.commit()
                if deleted:
                    logger.info("Purged %s expired transcriptions", deleted)
        except Exception:
            logger.exception("Retention purge failed")
        await asyncio.sleep(RETENTION_INTERVAL_SECONDS)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Fill it in the local .env file.")

    session_factory = create_session_factory(settings)

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.update.middleware(DatabaseSessionMiddleware(session_factory))
    dispatcher.include_router(router)

    retention_task = asyncio.create_task(
        _retention_loop(session_factory, settings.transcription_retention_days)
    )

    try:
        await dispatcher.start_polling(bot)
    finally:
        retention_task.cancel()
        with suppress(asyncio.CancelledError):
            await retention_task
        await close_openai_client()
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
