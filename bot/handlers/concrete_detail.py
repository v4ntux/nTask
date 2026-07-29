from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.queries import (
    complete_test_schedule,
    get_batch_by_id,
    get_schedule_by_id,
    get_test_schedules_for_batch,
    get_result_for_schedule,
    redistribute_pending_test_volumes,
    toggle_batch_notification,
    format_date,
)

router = Router()


def _get_tz_today() -> str:
    return datetime.now(tz=ZoneInfo("Asia/Tashkent")).date().isoformat()


async def render_batch_detail(db, batch_id: int, query: CallbackQuery) -> None:
    batch = await get_batch_by_id(db, batch_id)
    if batch is None:
        await query.answer("Партия не найдена", show_alert=True)
        return

    schedules = await get_test_schedules_for_batch(db, batch_id)
    notify_3 = bool(batch["notify_3_day"])
    notify_7 = bool(batch["notify_7_day"])
    notify_14 = bool(batch["notify_14_day"])
    notify_28 = bool(batch["notify_28_day"])

    total_volume = int(round(batch["volume"]))
    remaining = int(round(batch.get("remaining_volume", batch["volume"])))
    tested = total_volume - remaining

    completed_schedules = [sch for sch in schedules if sch["status"] == "completed"]
    pending_schedules = [
        sch for sch in schedules
        if sch["status"] == "pending" and sch["notify"] == 1 and int(round(sch["volume"])) > 0
    ]
    completed_schedules.sort(key=lambda x: x["days"])
    pending_schedules.sort(key=lambda x: x["days"])

    text_lines = [f"🧱 БЕТОН #{batch['id']}", ""]
    text_lines.append(f"Марка: {batch['grade']}")
    text_lines.append(f"📍 Объект: {batch['location']}")
    text_lines.append(f"🏷️ Пикетаж: {batch['picket']}")
    text_lines.append(f"📅 Дата заливки: {format_date(batch['poured_at'])}")
    text_lines.append("")
    text_lines.append("📦 ОБЪЁМ")
    text_lines.append("")
    text_lines.append(f"Всего кубиков: {total_volume}")
    text_lines.append(f"Испытано: {tested}")
    text_lines.append(f"Осталось: {remaining}")
    text_lines.append("")
    text_lines.append("🧪 ПЛАН ИСПЫТАНИЙ")

    if pending_schedules or completed_schedules:
        for sch in pending_schedules:
            text_lines.append(f"{sch['days']} дней — {int(round(sch['volume']))} кубика — ⏳ ожидает")
        for sch in completed_schedules:
            text_lines.append(f"{sch['days']} дней — {int(round(sch['volume']))} кубика — ✅ выполнено")
    else:
        text_lines.append("План испытаний пока пуст.")

    if pending_schedules:
        text_lines.append("")
    elif completed_schedules:
        text_lines.append("")
        text_lines.append("✅ ИСПЫТАНИЯ ЗАВЕРШЕНЫ")

    keyboard = []
    today = _get_tz_today()
    today_schedule = next(
        (sch for sch in pending_schedules if sch["scheduled_at"] == today),
        None,
    )
    if today_schedule is not None:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🧪 Выполнить испытание {today_schedule['days']}д — {int(round(today_schedule['volume']))} кубика",
                callback_data=f"complete_{today_schedule['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text=f"3 дня {'✅' if notify_3 else '❌'}",
            callback_data=f"toggle_batch_notify_{batch_id}_3",
        ),
        InlineKeyboardButton(
            text=f"7 дней {'✅' if notify_7 else '❌'}",
            callback_data=f"toggle_batch_notify_{batch_id}_7",
        ),
    ])
    keyboard.append([
        InlineKeyboardButton(
            text=f"14 дней {'✅' if notify_14 else '❌'}",
            callback_data=f"toggle_batch_notify_{batch_id}_14",
        ),
        InlineKeyboardButton(
            text=f"28 дней {'✅' if notify_28 else '❌'}",
            callback_data=f"toggle_batch_notify_{batch_id}_28",
        ),
    ])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="concrete_list")])

    await query.message.edit_text("\n".join(text_lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


async def render_complete_confirmation(db, schedule_id: int, query: CallbackQuery) -> None:
    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        await query.answer("Испытание не найдено", show_alert=True)
        return

    batch = await get_batch_by_id(db, schedule["batch_id"])
    if batch is None:
        await query.answer("Партия не найдена", show_alert=True)
        return

    await query.message.edit_text(
        f"🧪 ПОДТВЕРЖДЕНИЕ ИСПЫТАНИЯ\n\n"
        f"Марка: {batch['grade']}\n"
        f"Объект: {batch['location']}\n"
        f"Пикетаж: {batch['picket']}\n\n"
        f"Испытание: {schedule['days']} дней\n"
        f"Количество: {int(round(schedule['volume']))} кубика\n\n"
        f"Подтвердить выполнение?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_complete_{schedule_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_complete_{schedule_id}")],
        ]),
    )


@router.callback_query(lambda query: query.data.startswith("batch_"))
async def batch_detail_callback(query: CallbackQuery) -> None:
    try:
        batch_id = int(query.data.split("_")[1])
    except Exception:
        await query.answer("Неверный идентификатор партии", show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    await render_batch_detail(db, batch_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("toggle_batch_notify_"))
async def toggle_batch_notify(query: CallbackQuery) -> None:
    parts = query.data.split("_")
    if len(parts) != 5:
        await query.answer("Неверный идентификатор", show_alert=True)
        return

    try:
        batch_id = int(parts[3])
        days = int(parts[4])
    except Exception:
        await query.answer("Неверный идентификатор", show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    if days not in (3, 7, 14, 28):
        await query.answer("Неверный тип испытания", show_alert=True)
        return

    batch = await get_batch_by_id(db, batch_id)
    if batch is None:
        await query.answer("Партия не найдена", show_alert=True)
        return

    await toggle_batch_notification(db, batch_id, days)
    await redistribute_pending_test_volumes(db, batch_id)
    await query.answer("Настройка испытаний обновлена")
    await render_batch_detail(db, batch_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("complete_"))
async def complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[1])
    except Exception:
        await query.answer("Неверный идентификатор", show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    await render_complete_confirmation(db, schedule_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("confirm_complete_"))
async def confirm_complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[2])
    except Exception:
        await query.answer("Неверный идентификатор", show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        await query.answer("Испытание не найдено", show_alert=True)
        return

    await complete_test_schedule(db, schedule_id)
    await query.answer("Испытание подтверждено")
    await render_batch_detail(db, schedule["batch_id"], query)


@router.callback_query(lambda query: query.data and query.data.startswith("cancel_complete_"))
async def cancel_complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[2])
    except Exception:
        await query.answer("Неверный идентификатор", show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        await query.answer("Ошибка базы данных", show_alert=True)
        return

    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        await query.answer("Испытание не найдено", show_alert=True)
        return

    await query.answer("Отменено")
    await render_batch_detail(db, schedule["batch_id"], query)


def register_concrete_detail_handlers(dp) -> None:
    dp.include_router(router)
