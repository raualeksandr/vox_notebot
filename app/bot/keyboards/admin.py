from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    labels = (
        ("Pending payments", "admin:pending_payments"),
        ("Find user", "admin:find_user"),
        ("Add minutes", "admin:add_minutes"),
        ("Remove minutes", "admin:remove_minutes"),
        ("User balance", "admin:user_balance"),
        ("Stats", "admin:stats"),
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback)]
            for text, callback in labels
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
