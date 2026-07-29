from aiogram import Router
from aiogram.filters.command import CommandStart
from aiogram.types import Message

from bot.database.queries import create_user
from bot.keyboards.main import main_menu_keyboard
import bot.database as db_module

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    db = db_module.db
    if db is not None and message.from_user is not None:
        await create_user(
            db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

    text = (
        "Добро пожаловать 👋\n"
        "Выберите действие:\n"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(lambda query: query.data == "main_menu")
async def main_menu_callback(query):
    await query.answer()
    await query.message.edit_text(
        "Добро пожаловать 👋\nВыберите действие:",
        reply_markup=main_menu_keyboard(),
    )


def register_start_handlers(dp) -> None:
    dp.include_router(router)
