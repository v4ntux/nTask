from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def safe_edit_text(query: CallbackQuery, text: str, reply_markup=None, **kwargs):
    try:
        return await query.message.edit_text(text, reply_markup=reply_markup, **kwargs)
    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            await query.answer()
            return None
        raise
