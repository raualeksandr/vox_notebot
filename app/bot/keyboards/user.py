from decimal import Decimal

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def user_menu_keyboard(*, is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎙 Отправить voice")],
        [
            KeyboardButton(text="📚 История"),
            KeyboardButton(text="💰 Баланс"),
        ],
        [
            KeyboardButton(text="🛒 Купить минуты"),
            KeyboardButton(text="⚙️ Настройка"),
        ],
        [
            KeyboardButton(text="❓ Помощь"),
        ],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Админка")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


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


def transcription_actions_keyboard(transcription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧹 Очистить",
                    callback_data=f"text:clean:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="📝 Summary",
                    callback_data=f"text:summary:{transcription_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✅ Задачи",
                    callback_data=f"text:tasks:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="🔍 Ключевые мысли",
                    callback_data=f"key_points:{transcription_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Вопросы",
                    callback_data=f"questions:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="📌 Следующие шаги",
                    callback_data=f"next_steps:{transcription_id}",
                )
            ],
        ]
    )


def history_transcription_keyboard(transcription_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Текст",
                    callback_data=f"history:text:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="🧹 Очистить",
                    callback_data=f"text:clean:{transcription_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Summary",
                    callback_data=f"text:summary:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="✅ Задачи",
                    callback_data=f"text:tasks:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="🔍 Мысли",
                    callback_data=f"key_points:{transcription_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❓ Вопросы",
                    callback_data=f"questions:{transcription_id}",
                ),
                InlineKeyboardButton(
                    text="📌 Шаги",
                    callback_data=f"next_steps:{transcription_id}",
                ),
            ],
        ]
    )
