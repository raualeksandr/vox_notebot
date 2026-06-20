from decimal import Decimal

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.role_actions import ROLE_ACTIONS, PERSONAL_NOTES_ROLE_CALLBACKS


UNIVERSAL_ACTION_ROWS = (
    (
        ("🧹 Очистить", "text:clean"),
        ("📝 Саммари", "text:summary"),
    ),
    (
        ("✅ Задачи", "text:tasks"),
        ("🔍 Ключевые мысли", "key_points"),
    ),
    (
        ("❓ Вопросы", "questions"),
        ("📌 Следующие шаги", "next_steps"),
    ),
)

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
    *,
    visible_callback_keys: set[str] | None = None,
) -> list[list[InlineKeyboardButton]]:
    rows = []
    for row in ROLE_ACTIONS.get(profile_type, ()):
        visible_actions = [
            action
            for action in row
            if visible_callback_keys is None
            or action.callback_key in visible_callback_keys
        ]
        if not visible_actions:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=action.label,
                    callback_data=f"{action.callback_key}:{transcription_id}",
                )
                for action in visible_actions
            ]
        )
    return rows


def _universal_action_rows(
    transcription_id: int,
    *,
    visible_callback_keys: set[str] | None = None,
) -> list[list[InlineKeyboardButton]]:
    rows = []
    for row in UNIVERSAL_ACTION_ROWS:
        visible_actions = [
            (label, callback_key)
            for label, callback_key in row
            if visible_callback_keys is None
            or callback_key in visible_callback_keys
        ]
        if not visible_actions:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{callback_key}:{transcription_id}",
                )
                for label, callback_key in visible_actions
            ]
        )
    return rows


def _visible_role_callback_keys(profile_type: str) -> set[str] | None:
    if profile_type == "personal_notes":
        return PERSONAL_NOTES_ROLE_CALLBACKS
    return None


def _history_text_row(transcription_id: int) -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text="📄 Текст",
            callback_data=f"history:text:{transcription_id}",
        )
    ]


def _history_action_rows(
    transcription_id: int,
    *,
    visible_callback_keys: set[str] | None = None,
) -> list[list[InlineKeyboardButton]]:
    universal_rows = _universal_action_rows(
        transcription_id,
        visible_callback_keys=visible_callback_keys,
    )
    if not universal_rows:
        return [_history_text_row(transcription_id)]

    return [
        [
            *_history_text_row(transcription_id),
            *universal_rows[0],
        ],
        *universal_rows[1:],
    ]


def _append_role_action_rows(
    inline_keyboard: list[list[InlineKeyboardButton]],
    transcription_id: int,
    *,
    include_hr_actions: bool,
    include_pm_ba_actions: bool,
    include_founder_actions: bool,
    include_student_researcher_actions: bool,
    include_personal_notes_actions: bool,
) -> None:
    for profile_type in _enabled_role_profiles(
        include_hr_actions=include_hr_actions,
        include_pm_ba_actions=include_pm_ba_actions,
        include_founder_actions=include_founder_actions,
        include_student_researcher_actions=include_student_researcher_actions,
        include_personal_notes_actions=include_personal_notes_actions,
    ):
        inline_keyboard.extend(
            _role_action_rows(
                profile_type,
                transcription_id,
                visible_callback_keys=_visible_role_callback_keys(profile_type),
            )
        )


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
    visible_universal_callback_keys: set[str] | None = None,
    include_hr_actions: bool = False,
    include_pm_ba_actions: bool = False,
    include_founder_actions: bool = False,
    include_student_researcher_actions: bool = False,
    include_personal_notes_actions: bool = False,
) -> InlineKeyboardMarkup:
    inline_keyboard = _universal_action_rows(
        transcription_id,
        visible_callback_keys=visible_universal_callback_keys,
    )
    _append_role_action_rows(
        inline_keyboard,
        transcription_id,
        include_hr_actions=include_hr_actions,
        include_pm_ba_actions=include_pm_ba_actions,
        include_founder_actions=include_founder_actions,
        include_student_researcher_actions=include_student_researcher_actions,
        include_personal_notes_actions=include_personal_notes_actions,
    )

    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
    )


def history_transcription_keyboard(
    transcription_id: int,
    *,
    visible_universal_callback_keys: set[str] | None = None,
    include_hr_actions: bool = False,
    include_pm_ba_actions: bool = False,
    include_founder_actions: bool = False,
    include_student_researcher_actions: bool = False,
    include_personal_notes_actions: bool = False,
) -> InlineKeyboardMarkup:
    inline_keyboard = _history_action_rows(
        transcription_id,
        visible_callback_keys=visible_universal_callback_keys,
    )
    _append_role_action_rows(
        inline_keyboard,
        transcription_id,
        include_hr_actions=include_hr_actions,
        include_pm_ba_actions=include_pm_ba_actions,
        include_founder_actions=include_founder_actions,
        include_student_researcher_actions=include_student_researcher_actions,
        include_personal_notes_actions=include_personal_notes_actions,
    )

    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard,
    )
