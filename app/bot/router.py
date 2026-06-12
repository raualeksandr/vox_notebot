from aiogram import Router

from app.bot.handlers import admin, balance, buy, start, voice


router = Router(name="root")
router.include_routers(
    start.router,
    balance.router,
    buy.router,
    admin.router,
    voice.router,
)

