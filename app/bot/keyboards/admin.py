from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


ADMIN_PLAN_LABELS = {
    "free": "Free",
    "personal": "Personal",
    "professional": "Professional",
    "premium": "Premium HR",
}


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    labels = (
        ("Pending payments", "admin:pending_payments"),
        ("🔎 Найти пользователя", "admin:find_user"),
        ("User balance", "admin:user_balance"),
        ("💳 Сменить тариф", "admin:change_plan"),
        ("🎁 Выдать Premium HR Trial", "admin:grant_premium_trial"),
        ("➕ Добавить минуты вручную", "admin:add_minutes"),
        ("➖ Списать минуты вручную", "admin:remove_minutes"),
        ("Stats", "admin:stats"),
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback)]
            for text, callback in labels
        ]
    )


def user_card_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Выдать Premium HR Trial",
                    callback_data=f"admin:user:trial:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Сменить тариф",
                    callback_data=f"admin:user:change_plan:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить минуты вручную",
                    callback_data=f"admin:user:add_minutes:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Списать минуты вручную",
                    callback_data=f"admin:user:remove_minutes:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить карточку",
                    callback_data=f"admin:user:refresh:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в админку",
                    callback_data="admin:back",
                )
            ],
        ]
    )


def payment_review_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Confirm",
                    callback_data=f"admin:payment:confirm:{payment_id}",
                ),
                InlineKeyboardButton(
                    text="Reject",
                    callback_data=f"admin:payment:reject:{payment_id}",
                ),
            ]
        ]
    )


def plan_selection_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"admin:plan:set:{plan_key}:{user_id}",
                )
            ]
            for plan_key, label in ADMIN_PLAN_LABELS.items()
        ]
    )
