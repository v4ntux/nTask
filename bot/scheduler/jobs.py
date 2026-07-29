from datetime import date
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.queries import get_pending_tests_by_date, get_user_by_telegram
from bot.database.db import Database
from bot.utils.i18n import detect_language, t


def build_reminder_text(item: dict, language: str) -> str:
    return (
        f"{t(language, 'reminder_title')}\n"
        f"{t(language, 'reminder_grade', grade=item['grade'])}\n"
        f"{t(language, 'reminder_volume', volume=int(item['volume']))}\n"
        f"{t(language, 'reminder_poured', poured_at=item['poured_at'])}\n"
        f"{t(language, 'reminder_age', days=item['days'])}\n"
    )


def setup_scheduler(bot: Bot, db: Database) -> None:
    scheduler = AsyncIOScheduler()

    async def send_daily_reminders() -> None:
        target_date = date.today(tz=ZoneInfo("Asia/Tashkent")).isoformat()
        items = await get_pending_tests_by_date(db, target_date)
        for item in items:
            chat_id = item["telegram_id"]
            language = detect_language(None)
            user = await get_user_by_telegram(db, chat_id)
            if user is not None:
                language = user.get("language", language)
            text = build_reminder_text(item, language)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(language, "confirm_test"), callback_data=f"complete_{item['id']}")],
                [InlineKeyboardButton(text=t(language, "open_batch_button"), callback_data=f"batch_{item['batch_id']}")],
            ])
            await bot.send_message(chat_id, text, reply_markup=keyboard)

    scheduler.add_job(send_daily_reminders, "cron", hour=7, minute=0, timezone=ZoneInfo("Asia/Tashkent"))
    scheduler.start()
