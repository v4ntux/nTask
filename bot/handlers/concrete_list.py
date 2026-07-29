from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import bot.database as db_module
from bot.database.queries import get_batches_for_user, get_user_by_telegram, format_date
from bot.keyboards.main import main_menu_keyboard
from bot.utils.i18n import t, detect_language
from bot.utils.telegram import safe_edit_text

router = Router()


@router.callback_query(lambda query: query.data == "concrete_list")
async def list_batches_callback(query: CallbackQuery) -> None:
    language = detect_language(query.from_user.language_code if query.from_user else None)
    db = db_module.db
    if db is None or query.from_user is None:
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    user_id_row = await db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (query.from_user.id,))
    if user_id_row is None:
        await query.answer(t(language, "user_not_found"), show_alert=True)
        return

    user_id = user_id_row[0]
    batches = await get_batches_for_user(db, user_id)
    language = "ru"
    user = await get_user_by_telegram(db, query.from_user.id)
    if user is not None:
        language = user.get("language", "ru")

    if not batches:
        await safe_edit_text(
            query,
            t(language, "concrete_list_title") + t(language, "no_batches"),
            reply_markup=main_menu_keyboard(language),
        )
        return

    lines = [t(language, "batch_label", id=batch['id']) for batch in batches]
    keyboard_rows = []
    current_row = []
    for batch in batches:
        poured = format_date(batch['poured_at']) if batch.get('poured_at') else batch.get('poured_at')
        current_row.append(InlineKeyboardButton(text=poured, callback_data=f"batch_{batch['id']}"))
        if len(current_row) >= 2:
            keyboard_rows.append(current_row)
            current_row = []
    if current_row:
        keyboard_rows.append(current_row)

    keyboard_rows.append([InlineKeyboardButton(text=t(language, "main_menu_button"), callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await safe_edit_text(
        query,
        t(language, "concrete_list_title") + "\n".join(lines),
        reply_markup=markup,
    )


def register_concrete_list_handlers(dp) -> None:
    dp.include_router(router)
