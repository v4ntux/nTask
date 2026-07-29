from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.utils.i18n import t


def main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=t(language, "list_concrete_button"), callback_data="concrete_list"),
        InlineKeyboardButton(text=t(language, "add_concrete_button"), callback_data="concrete_add"),
        InlineKeyboardButton(text=t(language, "settings_button"), callback_data="settings"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
