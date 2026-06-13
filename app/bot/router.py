from aiogram import Router

from app.bot.handlers import admin, balance, buy, history, menu, start, voice


router = Router(name="root")
router.include_routers(
    start.router,
    balance.router,
    buy.router,
    history.router,
    admin.router,
    menu.router,
    voice.router,
)
