from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import bot.database as db_module
from bot.database.queries import get_batches_for_user, format_date
from bot.keyboards.main import main_menu_keyboard

router = Router()


@router.callback_query(lambda query: query.data == "concrete_list")
async def list_batches_callback(query: CallbackQuery) -> None:
    db = db_module.db
    if db is None or query.from_user is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    user_id_row = await db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (query.from_user.id,))
    if user_id_row is None:
        await query.answer("Пользователь не найден", show_alert=True)
        return

    user_id = user_id_row[0]
    batches = await get_batches_for_user(db, user_id)
    if not batches:
        await query.message.edit_text(
            "📋 Список бетона\n\nПока нет ни одной партии. Нажмите Добавить бетон.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = [f"Бетон #{batch['id']}" for batch in batches]
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

    keyboard_rows.append([InlineKeyboardButton(text="Главное меню", callback_data="main_menu")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await query.message.edit_text(
        "📋 Список бетона\n\n" + "\n".join(lines),
        reply_markup=markup,
    )


def register_concrete_list_handlers(dp) -> None:
    dp.include_router(router)
