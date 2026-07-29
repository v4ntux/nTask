from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command
import bot.database as db_module
from bot.database.queries import get_pending_tests_by_date
from bot.keyboards.main import main_menu_keyboard

router = Router()


@router.message(Command("today"))
async def today_notification_handler(message: Message) -> None:
    db = db_module.db
    if db is None:
        await message.answer("Ошибка базы данных.")
        return

    target_date = message.date.date().isoformat()
    items = await get_pending_tests_by_date(db, target_date)
    if not items:
        return

    text_lines = ["🧪 ИСПЫТАНИЯ НА СЕГОДНЯ"]
    for item in items:
        text_lines.append(
            f"\n🧱 Бетон #{item['batch_id']}\n"
            f"Марка: {item['grade']}\n"
            f"📍 {item['location']}\n"
            f"🏷 {item['picket']}\n"
            f"📅 Заливка: {item['poured_at']}\n"
            f"⏱ Испытание: {item['days']} дн.\n"
            f"📦 Количество: {int(item['volume'])}"
        )
        await message.answer(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🧪 Открыть бетон", callback_data=f"batch_{item['batch_id']}")]
            ]),
        )
        text_lines = ["🧪 ИСПЫТАНИЯ НА СЕГОДНЯ"]


def register_notification_handlers(dp) -> None:
    dp.include_router(router)
