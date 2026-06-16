from decimal import Decimal

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.role_actions import ROLE_ACTIONS


def user_menu_keyboard(*, is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎙 Отправить голосовое")],
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


def _role_action_rows(
    profile_type: str,
    transcription_id: int,
) -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                text=action.label,
                callback_data=f"{action.callback_key}:{transcription_id}",
            )
            for action in row
        ]
        for row in ROLE_ACTIONS.get(profile_type, ())
    ]


def _enabled_role_profiles(
    *,
    include_hr_actions: bool,
    include_pm_ba_actions: bool,
    include_founder_actions: bool,
    include_student_researcher_actions: bool,
    include_personal_notes_actions: bool,
) -> list[str]:
    enabled_profiles = []
    if include_hr_actions:
        enabled_profiles.append("hr_assessor")
    if include_pm_ba_actions:
        enabled_profiles.append("pm_ba")
    if include_founder_actions:
        enabled_profiles.append("founder")
    if include_student_researcher_actions:
        enabled_profiles.append("student_researcher")
    if include_personal_notes_actions:
        enabled_profiles.append("personal_notes")
    return enabled_profiles


def transcription_actions_keyboard(
    transcription_id: int,
    *,
    include_hr_actions: bool = False,
    include_pm_ba_actions: bool = False,
    include_founder_actions: bool = False,
    include_student_researcher_actions: bool = False,
    include_personal_notes_actions: bool = False,
) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="🧹 Очистить",
                callback_data=f"text:clean:{transcription_id}",
            ),
            InlineKeyboardButton(
                text="📝 Саммари",
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
    for profile_type in _enabled_role_profiles(
        include_hr_actions=include_hr_actions,
        include_pm_ba_actions=include_pm_ba_actions,
        include_founder_actions=include_founder_actions,
        include_student_researcher_actions=include_student_researcher_actions,
        include_personal_notes_actions=include_personal_notes_actions,
    ):
        inline_keyboard.extend(_role_action_rows(profile_type, transcription_id))

    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
    )


def history_transcription_keyboard(
    transcription_id: int,
    *,
    include_hr_actions: bool = False,
    include_pm_ba_actions: bool = False,
    include_founder_actions: bool = False,
    include_student_researcher_actions: bool = False,
    include_personal_notes_actions: bool = False,
) -> InlineKeyboardMarkup:
    inline_keyboard = [
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
                text="📝 Саммари",
                callback_data=f"text:summary:{transcription_id}",
            ),
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
            ),
        ],
    ]
    for profile_type in _enabled_role_profiles(
        include_hr_actions=include_hr_actions,
        include_pm_ba_actions=include_pm_ba_actions,
        include_founder_actions=include_founder_actions,
        include_student_researcher_actions=include_student_researcher_actions,
        include_personal_notes_actions=include_personal_notes_actions,
    ):
        inline_keyboard.extend(_role_action_rows(profile_type, transcription_id))

    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
    )
