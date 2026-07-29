from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def date_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="Сегодня", callback_data="date_today"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def grade_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="B12.5", callback_data="grade_B12.5"),
        InlineKeyboardButton(text="B25", callback_data="grade_B25"),
        InlineKeyboardButton(text="B27.5", callback_data="grade_B27.5"),
        InlineKeyboardButton(text="B30", callback_data="grade_B30"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def volume_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="3 кубика", callback_data="volume_3"),
        InlineKeyboardButton(text="6 кубиков", callback_data="volume_6"),
        InlineKeyboardButton(text="12 кубиков", callback_data="volume_12"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def tests_keyboard(selected: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for value in [3, 7, 14, 28]:
        mark = "✅" if value in selected else ""
        buttons.append(
            InlineKeyboardButton(text=f"{value} {mark}".strip(), callback_data=f"test_{value}"),
        )
    buttons.append(InlineKeyboardButton(text="Готово", callback_data="tests_confirm"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:4], [buttons[4]]])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Отмена", callback_data="cancel")]])
