from datetime import date
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.queries import get_pending_tests_by_date
from bot.database.db import Database


def build_reminder_text(item: dict) -> str:
    return (
        f"🧪 Сегодня испытание бетона\n"
        f"📍 {item['location']}\n"
        f"🧱 Марка: {item['grade']}\n"
        f"📦 Кубиков: {int(item['volume'])}\n"
        f"📅 Дата заливки: {item['poured_at']}\n"
        f"⏱ Возраст: {item['days']} дн.\n"
    )


def setup_scheduler(bot: Bot, db: Database) -> None:
    scheduler = AsyncIOScheduler()

    async def send_daily_reminders() -> None:
        target_date = date.today(tz=ZoneInfo("Asia/Tashkent")).isoformat()
        items = await get_pending_tests_by_date(db, target_date)
        for item in items:
            chat_id = item["telegram_id"]
            text = build_reminder_text(item)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"complete_{item['id']}")],
                [InlineKeyboardButton(text="📋 Подробнее", callback_data=f"batch_{item['batch_id']}")],
            ])
            await bot.send_message(chat_id, text, reply_markup=keyboard)

    scheduler.add_job(send_daily_reminders, "cron", hour=7, minute=0, timezone=ZoneInfo("Asia/Tashkent"))
    scheduler.start()
