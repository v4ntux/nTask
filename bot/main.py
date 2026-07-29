import asyncio
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
import bot.database as db_module
from bot.database.db import Database
from bot.handlers.start import register_start_handlers
from bot.handlers.concrete_add import register_concrete_add_handlers
from bot.handlers.concrete_list import register_concrete_list_handlers
from bot.handlers.notifications import register_notification_handlers
from bot.handlers.concrete_detail import register_concrete_detail_handlers
from bot.handlers.settings import register_settings_handlers
from bot.scheduler.jobs import setup_scheduler


async def main() -> None:
    default_props = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=config.BOT_TOKEN, default=default_props)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db = Database(config.DB_PATH)
    await db.setup()
    db_module.db = db

    register_start_handlers(dp)
    register_concrete_add_handlers(dp)
    register_concrete_list_handlers(dp)
    register_concrete_detail_handlers(dp)
    register_notification_handlers(dp)
    register_settings_handlers(dp)

    setup_scheduler(bot, db)

    print("Bot is starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
