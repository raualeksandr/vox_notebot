from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Balance, BalanceTransaction, Payment


PENDING_PAYMENT_STATUSES = ("pending", "paid_claimed")


def _as_minutes(value: Decimal | int | float | str) -> Decimal:
    minutes = Decimal(str(value))
    if minutes <= 0:
        raise ValueError("Minutes must be greater than zero.")
    return minutes


async def get_balance(session: AsyncSession, user_id: int) -> Balance | None:
    result = await session.execute(
        select(Balance).where(Balance.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_balance(
    session: AsyncSession,
    user_id: int,
) -> Balance:
    balance = await get_balance(session, user_id)
    if balance is None:
        balance = Balance(
            user_id=user_id,
            minutes_total=Decimal("0"),
            minutes_used=Decimal("0"),
            minutes_remaining=Decimal("0"),
        )
        session.add(balance)
        await session.flush()
    return balance


async def add_minutes(
    session: AsyncSession,
    user_id: int,
    minutes: Decimal | int | float | str,
    *,
    expires_at: datetime | None = None,
) -> Balance:
    amount = _as_minutes(minutes)
    balance = await get_or_create_balance(session, user_id)
    balance.minutes_total = Decimal(balance.minutes_total) + amount
    balance.minutes_remaining = Decimal(balance.minutes_remaining) + amount
    if expires_at is not None:
        balance.expires_at = expires_at
    await session.flush()
    return balance


async def set_balance_minutes(
    session: AsyncSession,
    user_id: int,
    minutes: Decimal | int | float | str,
) -> Balance:
    amount = _as_minutes(minutes)
    balance = await get_or_create_balance(session, user_id)
    balance.minutes_remaining = amount
    balance.minutes_total = Decimal(balance.minutes_used) + amount
    await session.flush()
    return balance


async def remove_minutes(
    session: AsyncSession,
    user_id: int,
    minutes: Decimal | int | float | str,
) -> Balance:
    amount = _as_minutes(minutes)
    balance = await get_or_create_balance(session, user_id)
    remaining = Decimal(balance.minutes_remaining)
    if remaining < amount:
        raise ValueError("Insufficient minute balance.")

    balance.minutes_used = Decimal(balance.minutes_used) + amount
    balance.minutes_remaining = remaining - amount
    await session.flush()
    return balance


async def create_balance_transaction(
    session: AsyncSession,
    *,
    user_id: int,
    transaction_type: str,
    minutes_delta: Decimal | int | float | str,
    reason: str | None = None,
    admin_id: int | None = None,
) -> BalanceTransaction:
    transaction = BalanceTransaction(
        user_id=user_id,
        type=transaction_type,
        minutes_delta=Decimal(str(minutes_delta)),
        reason=reason,
        admin_id=admin_id,
    )
    session.add(transaction)
    await session.flush()
    return transaction


async def create_pending_payment(
    session: AsyncSession,
    *,
    user_id: int,
    amount: Decimal | int | float | str,
    package_name: str,
    minutes: int,
    currency: str = "RUB",
    payment_method: str = "sbp",
    comment: str | None = None,
) -> Payment:
    if minutes <= 0:
        raise ValueError("Payment minutes must be greater than zero.")

    payment_amount = Decimal(str(amount))
    if payment_amount < 0:
        raise ValueError("Payment amount cannot be negative.")

    payment = Payment(
        user_id=user_id,
        amount=payment_amount,
        currency=currency,
        package_name=package_name,
        minutes=minutes,
        payment_method=payment_method,
        status="pending",
        comment=comment,
    )
    session.add(payment)
    await session.flush()
    return payment


async def mark_payment_as_paid_claimed(
    session: AsyncSession,
    payment_id: int,
) -> Payment:
    payment = await _get_payment_for_update(session, payment_id)
    if payment.status != "pending":
        raise ValueError("Only pending payments can be marked as paid.")

    payment.status = "paid_claimed"
    await session.flush()
    return payment


async def confirm_payment(
    session: AsyncSession,
    payment_id: int,
    *,
    admin_id: int,
) -> Payment:
    payment = await _get_payment_for_update(session, payment_id)
    if payment.status == "confirmed":
        return payment
    if payment.status not in PENDING_PAYMENT_STATUSES:
        raise ValueError("Payment cannot be confirmed in its current status.")

    payment.status = "confirmed"
    payment.confirmed_at = datetime.now(timezone.utc)
    payment.confirmed_by_admin_id = admin_id
    await add_minutes(session, payment.user_id, payment.minutes)
    await create_balance_transaction(
        session,
        user_id=payment.user_id,
        transaction_type="topup",
        minutes_delta=payment.minutes,
        reason=f"Confirmed payment #{payment.id}",
        admin_id=admin_id,
    )
    await session.flush()
    return payment


async def reject_payment(
    session: AsyncSession,
    payment_id: int,
) -> Payment:
    payment = await _get_payment_for_update(session, payment_id)
    if payment.status == "rejected":
        return payment
    if payment.status not in PENDING_PAYMENT_STATUSES:
        raise ValueError("Payment cannot be rejected in its current status.")

    payment.status = "rejected"
    await session.flush()
    return payment


async def get_pending_payments(session: AsyncSession) -> list[Payment]:
    query: Select[tuple[Payment]] = (
        select(Payment)
        .where(Payment.status.in_(PENDING_PAYMENT_STATUSES))
        .order_by(Payment.created_at.asc(), Payment.id.asc())
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_payment(session: AsyncSession, payment_id: int) -> Payment | None:
    return await session.get(Payment, payment_id)


async def get_recent_balance_transactions(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 3,
) -> list[BalanceTransaction]:
    result = await session.execute(
        select(BalanceTransaction)
        .where(BalanceTransaction.user_id == user_id)
        .order_by(BalanceTransaction.created_at.desc(), BalanceTransaction.id.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def has_free_grant(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(
        select(BalanceTransaction.id)
        .where(
            BalanceTransaction.user_id == user_id,
            BalanceTransaction.type == "free_grant",
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def _get_payment_for_update(
    session: AsyncSession,
    payment_id: int,
) -> Payment:
    result = await session.execute(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise LookupError(f"Payment {payment_id} was not found.")
    return payment


def seconds_to_billable_minutes(duration_seconds: int | float) -> Decimal:
    """Convert audio duration to fractional minutes without charging a user."""
    return Decimal(str(duration_seconds)) / Decimal("60")
