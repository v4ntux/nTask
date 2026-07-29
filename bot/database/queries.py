from datetime import datetime, timedelta
from typing import Any

from bot.database.db import Database


async def create_user(db: Database, telegram_id: int, username: str | None, first_name: str | None, last_name: str | None, language: str = "ru") -> int:
    await db.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, language) VALUES (?, ?, ?, ?, ?)",
        (telegram_id, username, first_name, last_name, language),
    )
    await db.execute(
        "UPDATE users SET username = ?, first_name = ?, last_name = ? WHERE telegram_id = ?",
        (username, first_name, last_name, telegram_id),
    )
    await db.commit()
    row = await db.fetchone(
        "SELECT id FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    return row[0]


async def create_batch(
    db: Database,
    user_id: int,
    grade: str,
    location: str,
    picket: str,
    volume: float,
    poured_at: str,
    notify_days: set[int],
) -> int:
    notify_3 = 1 if 3 in notify_days else 0
    notify_7 = 1 if 7 in notify_days else 0
    notify_14 = 1 if 14 in notify_days else 0
    notify_28 = 1 if 28 in notify_days else 0
    await db.execute(
        "INSERT INTO concrete_batches (user_id, grade, location, picket, volume, remaining_volume, poured_at, notify_3_day, notify_7_day, notify_14_day, notify_28_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, grade, location, picket, volume, volume, poured_at, notify_3, notify_7, notify_14, notify_28),
    )
    await db.commit()
    row = await db.fetchone(
        "SELECT id FROM concrete_batches WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    return row[0]


async def create_test_schedule(
    db: Database,
    batch_id: int,
    days: int,
    volume: float,
    scheduled_at: str,
) -> int:
    await db.execute(
        "INSERT INTO test_schedules (batch_id, days, volume, scheduled_at) VALUES (?, ?, ?, ?)",
        (batch_id, days, volume, scheduled_at),
    )
    await db.commit()
    row = await db.fetchone(
        "SELECT id FROM test_schedules WHERE batch_id = ? AND days = ?",
        (batch_id, days),
    )
    return row[0]


async def get_batches_for_user(db: Database, user_id: int) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        "SELECT id, grade, location, picket, volume, remaining_volume, poured_at FROM concrete_batches WHERE user_id = ? ORDER BY poured_at DESC",
        (user_id,),
    )
    return [dict(zip(["id", "grade", "location", "picket", "volume", "remaining_volume", "poured_at"], row)) for row in rows]


async def get_batch_by_id(db: Database, batch_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        "SELECT id, grade, location, picket, volume, remaining_volume, poured_at, notify_3_day, notify_7_day, notify_14_day, notify_28_day FROM concrete_batches WHERE id = ?",
        (batch_id,),
    )
    return None if row is None else dict(zip(["id", "grade", "location", "picket", "volume", "remaining_volume", "poured_at", "notify_3_day", "notify_7_day", "notify_14_day", "notify_28_day"], row))


async def get_test_schedules_for_batch(db: Database, batch_id: int) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        "SELECT id, days, volume, scheduled_at, status, notify FROM test_schedules WHERE batch_id = ? ORDER BY days",
        (batch_id,),
    )
    return [dict(zip(["id", "days", "volume", "scheduled_at", "status", "notify"], row)) for row in rows]


async def get_schedule_by_id(db: Database, schedule_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        "SELECT id, batch_id, days, volume, scheduled_at, status, notify FROM test_schedules WHERE id = ?",
        (schedule_id,),
    )
    return None if row is None else dict(zip(["id", "batch_id", "days", "volume", "scheduled_at", "status", "notify"], row))


async def set_schedule_notify(db: Database, schedule_id: int, notify: int) -> None:
    await db.execute(
        "UPDATE test_schedules SET notify = ? WHERE id = ?",
        (notify, schedule_id),
    )
    await db.commit()


async def get_pending_tests_by_date(db: Database, target_date: str) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        """
        SELECT u.telegram_id, ts.id, ts.batch_id, ts.days, ts.volume, ts.scheduled_at, ts.status, ts.notify,
               b.grade, b.location, b.picket, b.poured_at, b.volume AS total_volume
        FROM test_schedules ts
        JOIN concrete_batches b ON b.id = ts.batch_id
        JOIN users u ON u.id = b.user_id
        WHERE ts.status = 'pending' AND ts.scheduled_at = ? AND ts.notify = 1
        ORDER BY b.poured_at DESC
        """,
        (target_date,),
    )
    keys = [
        "telegram_id",
        "id",
        "batch_id",
        "days",
        "volume",
        "scheduled_at",
        "status",
        "notify",
        "grade",
        "location",
        "picket",
        "poured_at",
        "total_volume",
    ]
    return [dict(zip(keys, row)) for row in rows]


async def get_pending_schedules_for_batch(db: Database, batch_id: int) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        "SELECT id, days, volume, scheduled_at, status, notify FROM test_schedules WHERE batch_id = ? AND status = 'pending' ORDER BY days",
        (batch_id,),
    )
    return [dict(zip(["id", "days", "volume", "scheduled_at", "status", "notify"], row)) for row in rows]


async def redistribute_pending_test_volumes(db: Database, batch_id: int) -> None:
    batch = await get_batch_by_id(db, batch_id)
    if batch is None:
        return

    remaining_volume = int(round(batch.get("remaining_volume", batch["volume"])))
    if remaining_volume <= 0:
        await db.execute(
            "UPDATE test_schedules SET volume = 0, notify = 0 WHERE batch_id = ? AND status = 'pending'",
            (batch_id,),
        )
        await db.commit()
        return

    enabled_days = set()
    if batch.get("notify_3_day"):
        enabled_days.add(3)
    if batch.get("notify_7_day"):
        enabled_days.add(7)
    if batch.get("notify_14_day"):
        enabled_days.add(14)
    if batch.get("notify_28_day"):
        enabled_days.add(28)

    pending_schedules = await get_pending_schedules_for_batch(db, batch_id)
    existing_days = {sch["days"] for sch in pending_schedules}
    for day in sorted(enabled_days - existing_days):
        scheduled_at = get_due_date(batch["poured_at"], day)
        await create_test_schedule(db, batch_id, day, 0, scheduled_at)

    pending_schedules = await get_pending_schedules_for_batch(db, batch_id)
    active_schedules = [sch for sch in pending_schedules if sch["days"] in enabled_days]
    inactive_schedules = [sch for sch in pending_schedules if sch["days"] not in enabled_days]

    if active_schedules:
        active_schedules.sort(key=lambda x: x["days"])
        per_schedule = remaining_volume // len(active_schedules)
        remainder = remaining_volume % len(active_schedules)
        for index, sch in enumerate(active_schedules):
            new_volume = per_schedule + (1 if index < remainder else 0)
            await db.execute(
                "UPDATE test_schedules SET volume = ?, notify = 1 WHERE id = ?",
                (new_volume, sch["id"]),
            )

    for sch in inactive_schedules:
        await db.execute(
            "UPDATE test_schedules SET volume = 0, notify = 0 WHERE id = ?",
            (sch["id"],),
        )

    await db.commit()


async def get_all_users(db: Database) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        "SELECT id, telegram_id FROM users",
    )
    return [dict(zip(["id", "telegram_id"], row)) for row in rows]


async def get_user_by_telegram(db: Database, telegram_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        "SELECT id, language FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    return None if row is None else dict(zip(["id", "language"], row))


async def set_user_language(db: Database, telegram_id: int, language: str) -> None:
    await db.execute(
        "UPDATE users SET language = ? WHERE telegram_id = ?",
        (language, telegram_id),
    )
    await db.commit()


async def get_batch_notification_settings_by_batch(db: Database, batch_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        """
        SELECT id, notify_3_day, notify_7_day, notify_14_day, notify_28_day
        FROM concrete_batches
        WHERE id = ?
        """,
        (batch_id,),
    )
    return None if row is None else dict(zip(["batch_id", "notify_3_day", "notify_7_day", "notify_14_day", "notify_28_day"], row))


async def toggle_batch_notification(db: Database, batch_id: int, days: int) -> dict[str, Any] | None:
    field = None
    if days == 3:
        field = "notify_3_day"
    elif days == 7:
        field = "notify_7_day"
    elif days == 14:
        field = "notify_14_day"
    elif days == 28:
        field = "notify_28_day"
    if field is None:
        raise ValueError("Invalid notification field")
    await db.execute(f"UPDATE concrete_batches SET {field} = 1 - {field} WHERE id = ?", (batch_id,))
    await db.commit()
    row = await db.fetchone(
        "SELECT notify_3_day, notify_7_day, notify_14_day, notify_28_day FROM concrete_batches WHERE id = ?",
        (batch_id,),
    )
    return None if row is None else dict(zip(["notify_3_day", "notify_7_day", "notify_14_day", "notify_28_day"], row))


async def get_user_notification_settings_by_batch(db: Database, batch_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        """
        SELECT u.id, u.notify_3_day, u.notify_14_day
        FROM users u
        JOIN concrete_batches b ON b.user_id = u.id
        WHERE b.id = ?
        """,
        (batch_id,),
    )
    return None if row is None else dict(zip(["user_id", "notify_3_day", "notify_14_day"], row))


async def complete_test_schedule(db: Database, schedule_id: int, tested_volume: float | None = None, result: str = "passed") -> None:
    schedule = await get_schedule_by_id(db, schedule_id)
    if schedule is None:
        return
    if tested_volume is None:
        tested_volume = schedule["volume"]
    # mark schedule completed
    await db.execute(
        "UPDATE test_schedules SET status = 'completed' WHERE id = ?",
        (schedule_id,),
    )
    # determine batch
    batch_id = schedule["batch_id"]
    # record test result
    completed_at = datetime.now().isoformat()
    await db.execute(
        "INSERT INTO test_results (schedule_id, completed_at, result, comment, tested_volume) VALUES (?, ?, ?, ?, ?)",
        (schedule_id, completed_at, result, None, tested_volume),
    )
    # subtract tested volume from batch remaining_volume
    if batch_id is not None and tested_volume is not None:
        await db.execute(
            "UPDATE concrete_batches SET remaining_volume = CASE WHEN remaining_volume - ? < 0 THEN 0 ELSE remaining_volume - ? END WHERE id = ?",
            (tested_volume, tested_volume, batch_id),
        )
    await db.commit()


async def get_result_for_schedule(db: Database, schedule_id: int) -> dict[str, Any] | None:
    row = await db.fetchone(
        "SELECT id, schedule_id, completed_at, result, comment, tested_volume FROM test_results WHERE schedule_id = ? ORDER BY completed_at DESC LIMIT 1",
        (schedule_id,),
    )
    if row is None:
        return None
    return dict(zip(["id", "schedule_id", "completed_at", "result", "comment", "tested_volume"], row))


async def get_results_for_batch(db: Database, batch_id: int) -> list[dict[str, Any]]:
    rows = await db.fetchall(
        """
        SELECT tr.id, tr.schedule_id, tr.completed_at, tr.result, tr.comment, tr.tested_volume, ts.days
        FROM test_results tr
        JOIN test_schedules ts ON ts.id = tr.schedule_id
        WHERE ts.batch_id = ?
        ORDER BY tr.completed_at DESC
        """,
        (batch_id,),
    )
    return [dict(zip(["id", "schedule_id", "completed_at", "result", "comment", "tested_volume", "days"], row)) for row in rows]


async def get_completed_volume_for_batch(db: Database, batch_id: int) -> float:
    row = await db.fetchone(
        """
        SELECT IFNULL(SUM(IFNULL(tr.tested_volume, 0.0)), 0) FROM test_results tr
        JOIN test_schedules ts ON ts.id = tr.schedule_id
        WHERE ts.batch_id = ?
        """,
        (batch_id,),
    )
    return float(row[0]) if row is not None else 0.0


def normalize_date(date_str: str) -> str | None:
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date().isoformat()
    except ValueError:
        return None


def format_date(date_str: str) -> str:
    return datetime.fromisoformat(date_str).strftime("%d.%m.%Y")


def get_due_date(poured_date: str, days: int) -> str:
    date = datetime.fromisoformat(poured_date).date() + timedelta(days=days)
    return date.isoformat()
