from aiogram import Router
from aiogram.filters.command import CommandStart
from aiogram.types import Message

from bot.database.queries import create_user, get_user_by_telegram
from bot.keyboards.main import main_menu_keyboard
from bot.utils.i18n import t, detect_language
from bot.utils.telegram import safe_edit_text
import bot.database as db_module

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    db = db_module.db
    language = detect_language(message.from_user.language_code if message.from_user else None)
    if db is not None and message.from_user is not None:
        await create_user(
            db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language=language,
        )

    await message.answer(t(language, "main_menu_title"), reply_markup=main_menu_keyboard(language))


@router.callback_query(lambda query: query.data == "main_menu")
async def main_menu_callback(query):
    language = "ru"
    if query.from_user is not None and db_module.db is not None:
        user = await get_user_by_telegram(db_module.db, query.from_user.id)
        if user is not None:
            language = user.get("language", "ru")

    await query.answer()
    await safe_edit_text(
        query,
        t(language, "main_menu_title"),
        reply_markup=main_menu_keyboard(language),
    )


def register_start_handlers(dp) -> None:
    dp.include_router(router)
