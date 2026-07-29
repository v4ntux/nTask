from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import bot.database as db_module
from bot.database.queries import (
    complete_test_schedule,
    get_batch_by_id,
    get_schedule_by_id,
    get_test_schedules_for_batch,
    get_result_for_schedule,
    redistribute_pending_test_volumes,
    toggle_batch_notification,
    format_date,
    get_user_by_telegram,
)
from bot.utils.i18n import t
from bot.utils.telegram import safe_edit_text

router = Router()


async def _get_language(query: CallbackQuery) -> str:
    if query.from_user is None or db_module.db is None:
        return "ru"
    user = await get_user_by_telegram(db_module.db, query.from_user.id)
    return user.get("language", "ru") if user else "ru"


def _get_tz_today() -> str:
    return datetime.now(tz=ZoneInfo("Asia/Tashkent")).date().isoformat()


async def render_batch_detail(db, batch_id: int, query: CallbackQuery) -> None:
    language = await _get_language(query)
    batch = await get_batch_by_id(db, batch_id)
    if batch is None:
        await query.answer(t(language, "batch_not_found"), show_alert=True)
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

    text_lines = [t(language, "batch_label", id=batch['id']), ""]
    text_lines.append(t(language, "grade_label", grade=batch['grade']))
    text_lines.append(t(language, "location_label", location=batch['location']))
    text_lines.append(t(language, "picket_label", picket=batch['picket']))
    text_lines.append(t(language, "poured_label", poured_at=format_date(batch['poured_at'])))
    text_lines.append("")
    text_lines.append(t(language, "volume_total", total_volume=total_volume))
    text_lines.append(t(language, "volume_tested", tested=tested))
    text_lines.append(t(language, "volume_remaining", remaining=remaining))
    text_lines.append("")
    text_lines.append(t(language, "test_plan_title"))

    if pending_schedules or completed_schedules:
        for sch in pending_schedules:
            text_lines.append(t(language, "test_line", days=sch['days'], volume=int(round(sch['volume'])), status=t(language, "waiting_status")))
        for sch in completed_schedules:
            text_lines.append(t(language, "test_line", days=sch['days'], volume=int(round(sch['volume'])), status=t(language, "done_status")))
    else:
        text_lines.append(t(language, "plan_empty"))

    if pending_schedules:
        text_lines.append("")
    elif completed_schedules:
        text_lines.append("")
        text_lines.append(t(language, "tests_complete"))

    keyboard = []
    today = _get_tz_today()
    today_schedule = next(
        (sch for sch in pending_schedules if sch["scheduled_at"] == today),
        None,
    )
    if today_schedule is not None:
        keyboard.append([
            InlineKeyboardButton(
                text=t(language, "perform_test_button", days=today_schedule['days'], volume=int(round(today_schedule['volume']))),
                callback_data=f"complete_{today_schedule['id']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text=t(language, "notify_day", days=3, status="✅" if notify_3 else "❌"),
            callback_data=f"toggle_batch_notify_{batch_id}_3",
        ),
        InlineKeyboardButton(
            text=t(language, "notify_day", days=7, status="✅" if notify_7 else "❌"),
            callback_data=f"toggle_batch_notify_{batch_id}_7",
        ),
    ])
    keyboard.append([
        InlineKeyboardButton(
            text=t(language, "notify_day", days=14, status="✅" if notify_14 else "❌"),
            callback_data=f"toggle_batch_notify_{batch_id}_14",
        ),
        InlineKeyboardButton(
            text=t(language, "notify_day", days=28, status="✅" if notify_28 else "❌"),
            callback_data=f"toggle_batch_notify_{batch_id}_28",
        ),
    ])
    keyboard.append([InlineKeyboardButton(text=t(language, "back"), callback_data="concrete_list")])

    await safe_edit_text(
        query,
        "\n".join(text_lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


async def render_complete_confirmation(db, schedule_id: int, query: CallbackQuery) -> None:
    language = await _get_language(query)
    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        await query.answer(t(language, "test_not_found"), show_alert=True)
        return

    batch = await get_batch_by_id(db, schedule["batch_id"])
    if batch is None:
        await query.answer(t(language, "batch_not_found"), show_alert=True)
        return

    await safe_edit_text(
        query,
        f"{t(language, 'test_confirmation')}"
        f"{t(language, 'grade_label', grade=batch['grade'])}\n"
        f"{t(language, 'location_label', location=batch['location'])}\n"
        f"{t(language, 'picket_label', picket=batch['picket'])}\n\n"
        f"{schedule['days']} {t(language, 'days_label')}: {int(round(schedule['volume']))}\n"
        f"{t(language, 'confirm_completion')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(language, 'confirm_test'), callback_data=f"confirm_complete_{schedule_id}")],
            [InlineKeyboardButton(text=t(language, 'confirm_cancel'), callback_data=f"cancel_complete_{schedule_id}")],
        ]),
    )


@router.callback_query(lambda query: query.data.startswith("batch_"))
async def batch_detail_callback(query: CallbackQuery) -> None:
    try:
        batch_id = int(query.data.split("_")[1])
    except Exception:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_batch_id"), show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        language = await _get_language(query)
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    await render_batch_detail(db, batch_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("toggle_batch_notify_"))
async def toggle_batch_notify(query: CallbackQuery) -> None:
    parts = query.data.split("_")
    if len(parts) != 5:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    try:
        batch_id = int(parts[3])
        days = int(parts[4])
    except Exception:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        language = await _get_language(query)
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    if days not in (3, 7, 14, 28):
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    batch = await get_batch_by_id(db, batch_id)
    if batch is None:
        language = await _get_language(query)
        await query.answer(t(language, "batch_not_found"), show_alert=True)
        return

    await toggle_batch_notification(db, batch_id, days)
    await redistribute_pending_test_volumes(db, batch_id)
    language = await _get_language(query)
    await query.answer(t(language, "setting_updated"))
    await render_batch_detail(db, batch_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("complete_"))
async def complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[1])
    except Exception:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        language = await _get_language(query)
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    await render_complete_confirmation(db, schedule_id, query)


@router.callback_query(lambda query: query.data and query.data.startswith("confirm_complete_"))
async def confirm_complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[2])
    except Exception:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        language = await _get_language(query)
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        language = await _get_language(query)
        await query.answer(t(language, "test_not_found"), show_alert=True)
        return

    await complete_test_schedule(db, schedule_id)
    language = await _get_language(query)
    await query.answer(t(language, "test_confirmed"))
    await render_batch_detail(db, schedule["batch_id"], query)


@router.callback_query(lambda query: query.data and query.data.startswith("cancel_complete_"))
async def cancel_complete_test_callback(query: CallbackQuery) -> None:
    try:
        schedule_id = int(query.data.split("_")[2])
    except Exception:
        language = await _get_language(query)
        await query.answer(t(language, "invalid_id"), show_alert=True)
        return

    import bot.database as db_module

    db = db_module.db
    if db is None:
        language = await _get_language(query)
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        language = await _get_language(query)
        await query.answer(t(language, "test_not_found"), show_alert=True)
        return

    language = await _get_language(query)
    await query.answer(t(language, "cancelled"))
    await render_batch_detail(db, schedule["batch_id"], query)


def register_concrete_detail_handlers(dp) -> None:
    dp.include_router(router)
