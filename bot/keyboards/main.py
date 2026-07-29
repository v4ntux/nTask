from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text="📋 Список бетона", callback_data="concrete_list"),
        InlineKeyboardButton(text="➕ Добавить бетон", callback_data="concrete_add"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
