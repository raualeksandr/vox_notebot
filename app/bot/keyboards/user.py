from decimal import Decimal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def packages_keyboard(
    *,
    free_minutes: int,
    friends_minutes: int,
    power_minutes: int,
    friends_price: Decimal,
    power_price: Decimal,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Free - {free_minutes} минут / месяц - 0 ₽",
                    callback_data="package:free",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Friends - {friends_minutes} минут - {friends_price:g} ₽",
                    callback_data="package:friends",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Power - {power_minutes} минут - {power_price:g} ₽",
                    callback_data="package:power",
                )
            ],
        ]
    )


def payment_claim_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Я оплатил",
                    callback_data=f"payment:claimed:{payment_id}",
                )
            ]
        ]
    )
