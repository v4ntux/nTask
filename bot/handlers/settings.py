from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import bot.database as db_module
from bot.database.queries import get_user_by_telegram, set_user_language
from bot.keyboards.main import main_menu_keyboard
from bot.utils.i18n import t, detect_language
from bot.utils.telegram import safe_edit_text

router = Router()


async def _get_language(query: CallbackQuery) -> str:
    db = db_module.db
    if db is None or query.from_user is None:
        return "ru"
    user = await get_user_by_telegram(db, query.from_user.id)
    if user is None:
        return "ru"
    return user.get("language", "ru")


@router.callback_query(lambda query: query.data == "settings")
async def settings_callback(query: CallbackQuery) -> None:
    language = await _get_language(query)
    await query.answer()
    await safe_edit_text(
        query,
        t(language, "settings_title") + "\n\n" + t(language, "choose_language"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(language, "language_ru"), callback_data="set_lang_ru")],
            [InlineKeyboardButton(text=t(language, "language_en"), callback_data="set_lang_en")],
            [InlineKeyboardButton(text=t(language, "back"), callback_data="main_menu")],
        ]),
    )


@router.callback_query(lambda query: query.data in ("set_lang_ru", "set_lang_en"))
async def set_language_callback(query: CallbackQuery) -> None:
    language = detect_language(query.from_user.language_code if query.from_user else None)
    db = db_module.db
    if db is None or query.from_user is None:
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    language = "ru" if query.data == "set_lang_ru" else "en"
    await set_user_language(db, query.from_user.id, language)
    await query.answer(t(language, "language_selected", language=t(language, f"language_{language}")))
    await safe_edit_text(
        query,
        t(language, "language_selected", language=t(language, f"language_{language}")),
        reply_markup=main_menu_keyboard(language),
    )


def register_settings_handlers(dp) -> None:
    dp.include_router(router)
