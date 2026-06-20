from dataclasses import dataclass
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.user import packages_keyboard, payment_claim_keyboard
from app.config import get_settings
from app.services.billing import (
    add_minutes,
    create_balance_transaction,
    create_pending_payment,
    get_payment,
    has_free_grant,
    mark_payment_as_paid_claimed,
)
from app.services.plans import get_plan
from app.services.users import get_or_create_user


router = Router(name="buy")


@dataclass(frozen=True)
class Package:
    name: str
    minutes: int
    price: Decimal


@router.message(Command("buy"))
async def buy_command(message: Message) -> None:
    settings = get_settings()
    telegram_user = message.from_user
    telegram_id_text = str(telegram_user.id) if telegram_user else "-"
    free_plan = get_plan("free")
    personal_plan = get_plan("personal")
    premium_plan = get_plan("premium")
    await message.answer(
        "Тарифы:\n"
        f"Free - {free_plan['minutes']} минут, fast-транскрибация, "
        "Очистить и Саммари.\n"
        f"Personal - {personal_plan['price']} RUB / "
        f"{personal_plan['minutes']} минут, личные заметки.\n"
        f"Premium HR - {premium_plan['price']} RUB / "
        f"{premium_plan['minutes']} минут, premium-транскрибация и "
        "HR-функции для оценщиков.\n\n"
        "Professional - internal/legacy, не основной публичный тариф.\n\n"
        "Для выдачи тарифа администратору нужен ваш Telegram ID.\n"
        f"Ваш Telegram ID: {telegram_id_text}\n\n"
        "После оплаты администратор подтверждает тариф и выдаёт пакет минут. "
        "Автоматической оплаты пока нет.\n\n"
        "Выберите тариф:",
        reply_markup=packages_keyboard(
            free_minutes=settings.default_free_minutes,
            friends_minutes=settings.friends_package_minutes,
            power_minutes=settings.power_package_minutes,
            friends_price=settings.friends_package_price,
            power_price=settings.power_package_price,
        ),
    )


@router.callback_query(F.data.startswith("package:"))
async def select_package(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_user = callback.from_user
    settings = get_settings()
    user = await get_or_create_user(
        session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    package_code = (callback.data or "").partition(":")[2]

    if package_code == "free":
        if await has_free_grant(session, user.id):
            await callback.answer("Free-пакет уже был начислен.", show_alert=True)
            return

        await add_minutes(session, user.id, settings.default_free_minutes)
        await create_balance_transaction(
            session,
            user_id=user.id,
            transaction_type="free_grant",
            minutes_delta=settings.default_free_minutes,
            reason="Стартовый Free-пакет",
        )
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                f"Начислено {settings.default_free_minutes} бесплатных минут."
            )
        return

    packages = {
        "friends": Package(
            "Personal",
            settings.friends_package_minutes,
            settings.friends_package_price,
        ),
        "power": Package(
            "Premium HR",
            settings.power_package_minutes,
            settings.power_package_price,
        ),
    }
    package = packages.get(package_code)
    if package is None:
        await callback.answer("Неизвестный пакет.", show_alert=True)
        return
    if package.price <= 0:
        await callback.answer(
            "Цена пакета пока не настроена администратором.",
            show_alert=True,
        )
        return

    payment = await create_pending_payment(
        session,
        user_id=user.id,
        amount=package.price,
        package_name=package.name,
        minutes=package.minutes,
        comment=settings.sbp_payment_comment or None,
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Переведите оплату по СБП:\n"
            f"Номер: {settings.sbp_phone}\n"
            f"Банк: {settings.sbp_bank_name}\n"
            f"Получатель: {settings.sbp_recipient_name}\n"
            f"Комментарий: {settings.sbp_payment_comment}\n\n"
            "После оплаты отправьте администратору: выбранный тариф, "
            "подтверждение оплаты и ваш Telegram ID.\n"
            f"Ваш Telegram ID: {callback.from_user.id}\n\n"
            "Затем нажмите кнопку 'Я оплатил'.",
            reply_markup=payment_claim_keyboard(payment.id),
        )


@router.callback_query(F.data.startswith("payment:claimed:"))
async def payment_claimed(callback: CallbackQuery, session: AsyncSession) -> None:
    payment_id_text = (callback.data or "").rsplit(":", maxsplit=1)[-1]
    if not payment_id_text.isdigit():
        await callback.answer("Некорректная заявка.", show_alert=True)
        return

    payment = await get_payment(session, int(payment_id_text))
    if payment is None:
        await callback.answer("Платёж не найден.", show_alert=True)
        return

    settings = get_settings()
    user = await get_or_create_user(
        session,
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        language_code=callback.from_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    if payment.user_id != user.id:
        await callback.answer("Нет доступа к этому платежу.", show_alert=True)
        return
    if payment.status == "paid_claimed":
        await callback.answer("Платёж уже отправлен на проверку.", show_alert=True)
        return

    try:
        await mark_payment_as_paid_claimed(session, payment.id)
    except ValueError:
        await callback.answer("Статус платежа уже изменён.", show_alert=True)
        return

    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Платёж отправлен на проверку. После подтверждения админом "
            "минуты будут начислены."
        )
