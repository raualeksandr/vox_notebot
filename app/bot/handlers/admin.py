from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.admin import admin_menu_keyboard, payment_review_keyboard
from app.config import get_settings
from app.db.models import Payment, Transcription, User
from app.services.billing import (
    add_minutes,
    confirm_payment,
    create_balance_transaction,
    get_balance,
    get_pending_payments,
    reject_payment,
    remove_minutes,
)
from app.services.users import (
    get_or_create_user,
    get_user_by_id,
    get_user_by_telegram_id,
    get_user_by_username,
)


router = Router(name="admin")


class AdminStates(StatesGroup):
    lookup_user = State()
    adjustment_target = State()
    adjustment_minutes = State()


def _is_admin(telegram_id: int) -> bool:
    return get_settings().is_admin(telegram_id)


async def _resolve_user(session: AsyncSession, query: str) -> User | None:
    normalized = query.strip()
    if normalized.lstrip("-").isdigit():
        return await get_user_by_telegram_id(session, int(normalized))
    return await get_user_by_username(session, normalized)


async def _send_notification(
    message: Message,
    telegram_id: int,
    text: str,
) -> None:
    try:
        await message.bot.send_message(telegram_id, text)
    except TelegramAPIError:
        pass


@router.message(Command("admin"))
async def admin_command(message: Message, session: AsyncSession) -> None:
    telegram_user = message.from_user
    if telegram_user is None or not _is_admin(telegram_user.id):
        await message.answer("Нет доступа")
        return

    settings = get_settings()
    await get_or_create_user(
        session,
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
        admin_telegram_ids=settings.admin_telegram_ids,
    )
    await message.answer("Панель администратора:", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:pending_payments")
async def pending_payments(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    payments = await get_pending_payments(session)
    await callback.answer()
    if callback.message is None:
        return
    if not payments:
        await callback.message.answer("Ожидающих платежей нет.")
        return

    for payment in payments:
        user = await get_user_by_id(session, payment.user_id)
        username = f"@{user.username}" if user and user.username else "-"
        telegram_id = user.telegram_id if user else "-"
        created_at = payment.created_at.strftime("%Y-%m-%d %H:%M")
        await callback.message.answer(
            f"Payment #{payment.id}\n"
            f"Telegram ID: {telegram_id}\n"
            f"Username: {username}\n"
            f"Пакет: {payment.package_name}\n"
            f"Сумма: {payment.amount} {payment.currency}\n"
            f"Минуты: {payment.minutes}\n"
            f"Статус: {payment.status}\n"
            f"Создан: {created_at}",
            reply_markup=payment_review_keyboard(payment.id),
        )


@router.callback_query(F.data.startswith("admin:payment:confirm:"))
async def confirm_payment_callback(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id_text = (callback.data or "").rsplit(":", maxsplit=1)[-1]
    if not payment_id_text.isdigit():
        await callback.answer("Некорректный платёж.", show_alert=True)
        return

    try:
        payment = await confirm_payment(
            session,
            int(payment_id_text),
            admin_id=callback.from_user.id,
        )
    except (LookupError, ValueError) as error:
        await callback.answer(str(error), show_alert=True)
        return

    user = await get_user_by_id(session, payment.user_id)
    balance = await get_balance(session, payment.user_id)
    await callback.answer("Платёж подтверждён.")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        if user and balance:
            await _send_notification(
                callback.message,
                user.telegram_id,
                f"Ваш платёж подтверждён. Начислено {payment.minutes} минут. "
                f"Текущий баланс: {balance.minutes_remaining} минут.",
            )


@router.callback_query(F.data.startswith("admin:payment:reject:"))
async def reject_payment_callback(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    payment_id_text = (callback.data or "").rsplit(":", maxsplit=1)[-1]
    if not payment_id_text.isdigit():
        await callback.answer("Некорректный платёж.", show_alert=True)
        return

    try:
        payment = await reject_payment(session, int(payment_id_text))
    except (LookupError, ValueError) as error:
        await callback.answer(str(error), show_alert=True)
        return

    user = await get_user_by_id(session, payment.user_id)
    await callback.answer("Платёж отклонён.")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        if user:
            await _send_notification(
                callback.message,
                user.telegram_id,
                "Ваш платёж отклонён. Если это ошибка, напишите в поддержку.",
            )


@router.callback_query(F.data.in_({"admin:find_user", "admin:user_balance"}))
async def request_user_lookup(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AdminStates.lookup_user)
    await state.update_data(lookup_mode=callback.data)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите telegram_id или @username пользователя.")


@router.message(AdminStates.lookup_user)
async def show_user_lookup(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id):
        await state.clear()
        await message.answer("Нет доступа")
        return

    user = await _resolve_user(session, message.text or "")
    if user is None:
        await message.answer("Пользователь не найден.")
        return

    balance = await get_balance(session, user.id)
    remaining = balance.minutes_remaining if balance else Decimal("0")
    await message.answer(
        f"User ID: {user.id}\n"
        f"Telegram ID: {user.telegram_id}\n"
        f"Username: @{user.username if user.username else '-'}\n"
        f"Имя: {user.first_name or '-'}\n"
        f"Роль: {user.role}\n"
        f"Заблокирован: {'да' if user.is_blocked else 'нет'}\n"
        f"Баланс: {remaining} минут"
    )
    await state.clear()


@router.callback_query(F.data.in_({"admin:add_minutes", "admin:remove_minutes"}))
async def request_adjustment_target(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    operation = "add" if callback.data == "admin:add_minutes" else "remove"
    await state.set_state(AdminStates.adjustment_target)
    await state.update_data(operation=operation)
    await callback.answer()
    if callback.message:
        await callback.message.answer("Введите telegram_id или @username пользователя.")


@router.message(AdminStates.adjustment_target)
async def receive_adjustment_target(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id):
        await state.clear()
        await message.answer("Нет доступа")
        return

    user = await _resolve_user(session, message.text or "")
    if user is None:
        await message.answer("Пользователь не найден. Попробуйте ещё раз.")
        return

    await state.update_data(target_user_id=user.id)
    await state.set_state(AdminStates.adjustment_minutes)
    await message.answer("Введите количество минут положительным числом.")


@router.message(AdminStates.adjustment_minutes)
async def receive_adjustment_minutes(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if message.from_user is None or not _is_admin(message.from_user.id):
        await state.clear()
        await message.answer("Нет доступа")
        return

    try:
        minutes = Decimal((message.text or "").strip().replace(",", "."))
        if minutes <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("Введите положительное число минут.")
        return

    data = await state.get_data()
    target_user_id = int(data["target_user_id"])
    operation = str(data["operation"])
    target_user = await get_user_by_id(session, target_user_id)
    if target_user is None:
        await state.clear()
        await message.answer("Пользователь больше не найден.")
        return

    try:
        if operation == "add":
            balance = await add_minutes(session, target_user_id, minutes)
            delta = minutes
            reason = "Ручное начисление администратором"
        else:
            balance = await remove_minutes(session, target_user_id, minutes)
            delta = -minutes
            reason = "Ручное списание администратором"
    except ValueError:
        await message.answer("Недостаточно минут для списания.")
        return

    await create_balance_transaction(
        session,
        user_id=target_user_id,
        transaction_type="manual_adjustment",
        minutes_delta=delta,
        reason=reason,
        admin_id=message.from_user.id,
    )
    await message.answer(
        f"Готово. Текущий баланс пользователя: "
        f"{balance.minutes_remaining} минут."
    )
    await _send_notification(
        message,
        target_user.telegram_id,
        f"Администратор изменил ваш баланс на {delta:+} минут. "
        f"Текущий баланс: {balance.minutes_remaining} минут.",
    )
    await state.clear()


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    users_count = await session.scalar(select(func.count(User.id))) or 0
    payments_count = await session.scalar(select(func.count(Payment.id))) or 0
    pending_count = await session.scalar(
        select(func.count(Payment.id)).where(
            Payment.status.in_(("pending", "paid_claimed"))
        )
    ) or 0
    transcriptions_count = await session.scalar(
        select(func.count(Transcription.id))
    ) or 0

    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"Пользователей: {users_count}\n"
            f"Платежей: {payments_count}\n"
            f"Ожидают проверки: {pending_count}\n"
            f"Транскрибаций: {transcriptions_count}"
        )
