from aiogram import Router

from app.bot.handlers import admin, balance, buy, history, menu, onboarding, start, voice


router = Router(name="root")
router.include_routers(
    start.router,
    onboarding.router,
    balance.router,
    buy.router,
    history.router,
    admin.router,
    menu.router,
    voice.router,
)
