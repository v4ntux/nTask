from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.i18n import t


def date_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=t(language, "today_button"), callback_data="date_today"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def grade_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="B12.5", callback_data="grade_B12.5"),
        InlineKeyboardButton(text="B25", callback_data="grade_B25"),
        InlineKeyboardButton(text="B27.5", callback_data="grade_B27.5"),
        InlineKeyboardButton(text="B30", callback_data="grade_B30"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def volume_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=t(language, "volume_3"), callback_data="volume_3"),
        InlineKeyboardButton(text=t(language, "volume_6"), callback_data="volume_6"),
        InlineKeyboardButton(text=t(language, "volume_12"), callback_data="volume_12"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def tests_keyboard(language: str, selected: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for value in [3, 7, 14, 28]:
        mark = "✅" if value in selected else ""
        buttons.append(
            InlineKeyboardButton(text=f"{value} {mark}".strip(), callback_data=f"test_{value}"),
        )
    buttons.append(InlineKeyboardButton(text=t(language, "done_button"), callback_data="tests_confirm"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:4], [buttons[4]]])


def cancel_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(language, "cancel_button"), callback_data="cancel")]])
