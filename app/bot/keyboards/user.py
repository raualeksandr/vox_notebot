from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def packages_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Free - 30 минут", callback_data="package:free")],
            [
                InlineKeyboardButton(
                    text="Friends - 300 минут",
                    callback_data="package:friends",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Power - 1000 минут",
                    callback_data="package:power",
                )
            ],
        ]
    )

