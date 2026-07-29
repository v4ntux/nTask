from aiogram import Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.filters import Command
import bot.database as db_module
from bot.database.queries import get_pending_tests_by_date
from bot.keyboards.main import main_menu_keyboard
from bot.utils.i18n import t, detect_language
from bot.utils.i18n import t, detect_language

router = Router()


@router.message(Command("today"))
async def today_notification_handler(message: Message) -> None:
    language = detect_language(message.from_user.language_code if message.from_user else None)
    db = db_module.db
    if db is None:
        await message.answer(t(language, "db_error"))
        return

    target_date = message.date.date().isoformat()
    items = await get_pending_tests_by_date(db, target_date)
    if not items:
        return

    text_lines = [t(language, "tests_today_title")]
    for item in items:
        text_lines.append(
            f"\n{t(language, 'batch_label', id=item['batch_id'])}\n"
            f"{t(language, 'grade_label', grade=item['grade'])}\n"
            f"📍 {item['location']}\n"
            f"🏷 {item['picket']}\n"
            f"📅 {t(language, 'poured_label', poured_at=item['poured_at'])}\n"
            f"⏱ {item['days']} {t(language, 'days_label')}\n"
            f"📦 {t(language, 'volume_total', total_volume=int(item['volume']))}"
        )
        await message.answer(
            "\n".join(text_lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(language, "open_batch_button"), callback_data=f"batch_{item['batch_id']}" )]
            ]),
        )
        text_lines = [t(language, "tests_today_title")]


def register_notification_handlers(dp) -> None:
    dp.include_router(router)
