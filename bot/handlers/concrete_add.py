from datetime import date
from aiogram import Router
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.database as db_module
from bot.database.queries import (
    create_batch,
    create_test_schedule,
    get_user_by_telegram,
    format_date,
    get_due_date,
    normalize_date,
)
from bot.keyboards.add import (
    cancel_keyboard,
    date_keyboard,
    grade_keyboard,
    tests_keyboard,
    volume_keyboard,
)
from bot.keyboards.main import main_menu_keyboard
from bot.states.concrete import ConcreteStates
from bot.utils.i18n import t, detect_language
from bot.utils.telegram import safe_edit_text

router = Router()


async def _get_language_from_user(user) -> str:
    db = db_module.db
    if user is None:
        return detect_language(None)
    language = detect_language(user.language_code)
    if db is None:
        return language
    user_row = await get_user_by_telegram(db, user.id)
    return user_row.get("language", language) if user_row else language


async def _get_language(query: CallbackQuery) -> str:
    return await _get_language_from_user(query.from_user)


@router.callback_query(lambda query: query.data == "concrete_add")
async def start_add_callback(query: CallbackQuery, state: FSMContext) -> None:
    language = await _get_language(query)
    await state.clear()
    await query.answer()
    await safe_edit_text(
        query,
        t(language, "choose_date"),
        reply_markup=date_keyboard(language),
    )
    await state.set_state(ConcreteStates.date)


@router.callback_query(lambda query: query.data == "date_today", StateFilter(ConcreteStates.date))
async def choose_today_callback(query: CallbackQuery, state: FSMContext) -> None:
    language = await _get_language(query)
    poured_at = date.today().isoformat()
    await state.update_data(poured_at=poured_at)
    await query.answer(t(language, "today_selected"))
    await safe_edit_text(
        query,
        t(language, "choose_grade"),
        reply_markup=grade_keyboard(language),
    )
    await state.set_state(ConcreteStates.grade)


@router.message(ConcreteStates.date)
async def enter_date_handler(message: Message, state: FSMContext) -> None:
    language = await _get_language_from_user(message.from_user)
    poured_at = normalize_date(message.text)
    if poured_at is None:
        await message.answer(
            t(language, "invalid_date"),
            reply_markup=date_keyboard(language),
        )
        return
    await state.update_data(poured_at=poured_at)
    await message.answer(
        t(language, "choose_grade"),
        reply_markup=grade_keyboard(language),
    )
    await state.set_state(ConcreteStates.grade)


@router.callback_query(lambda query: query.data.startswith("grade_"), StateFilter(ConcreteStates.grade))
async def choose_grade_callback(query: CallbackQuery, state: FSMContext) -> None:
    grade = query.data.replace("grade_", "")
    language = await _get_language(query)
    await state.update_data(grade=grade)
    await query.answer(t(language, "grade_label", grade=grade))
    await safe_edit_text(
        query,
        t(language, "enter_location"),
        reply_markup=cancel_keyboard(language),
    )
    await state.set_state(ConcreteStates.location)


@router.message(ConcreteStates.location)
async def enter_location_handler(message: Message, state: FSMContext) -> None:
    language = await _get_language_from_user(message.from_user)
    await state.update_data(location=message.text.strip())
    await message.answer(
        t(language, "enter_picket"),
        reply_markup=cancel_keyboard(language),
    )
    await state.set_state(ConcreteStates.picket)


@router.message(ConcreteStates.picket)
async def enter_picket_handler(message: Message, state: FSMContext) -> None:
    language = await _get_language_from_user(message.from_user)
    await state.update_data(picket=message.text.strip())
    await message.answer(
        t(language, "choose_volume"),
        reply_markup=volume_keyboard(language),
    )
    await state.set_state(ConcreteStates.volume)


@router.callback_query(lambda query: query.data.startswith("volume_"), StateFilter(ConcreteStates.volume))
async def choose_volume_callback(query: CallbackQuery, state: FSMContext) -> None:
    volume = float(query.data.replace("volume_", ""))
    await state.update_data(volume=volume)
    language = await _get_language(query)
    await query.answer(t(language, "volume_total", total_volume=int(volume)))

    await safe_edit_text(
        query,
        t(language, "choose_test_days_default"),
        reply_markup=tests_keyboard(language, {7, 28}),
    )
    await state.update_data(tests={7, 28})
    await state.set_state(ConcreteStates.tests)


@router.callback_query(lambda query: query.data.startswith("test_"), StateFilter(ConcreteStates.tests))
async def toggle_test_callback(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("tests", {7, 28}))
    day = int(query.data.replace("test_", ""))
    if day in selected:
        selected.remove(day)
    else:
        selected.add(day)
    if not selected:
        selected = {7, 28}
    await state.update_data(tests=selected)
    language = await _get_language(query)
    await query.answer(t(language, "done_button"))
    await safe_edit_text(
        query,
        t(language, "choose_test_days"),
        reply_markup=tests_keyboard(language, selected),
    )


@router.callback_query(lambda query: query.data == "tests_confirm", StateFilter(ConcreteStates.tests))
async def confirm_tests_callback(query: CallbackQuery, state: FSMContext) -> None:
    language = await _get_language(query)
    data = await state.get_data()
    if not data.get("tests"):
        await query.answer(t(language, "select_at_least_one_day"), show_alert=True)
        return

    db = db_module.db
    if db is None or query.from_user is None:
        await query.answer(t(language, "db_error"), show_alert=True)
        return

    poured_at = data["poured_at"]
    grade = data["grade"]
    location = data["location"]
    picket = data["picket"]
    volume = data["volume"]
    days = sorted(data["tests"])

    user_id_row = await db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (query.from_user.id,))
    if user_id_row is None:
        await query.answer(t(language, "user_not_found"), show_alert=True)
        return

    user_id = user_id_row[0]
    batch_id = await create_batch(db, user_id, grade, location, picket, volume, poured_at, set(days))

    base = int(volume) // len(days)
    remainder = int(volume) % len(days)
    schedule_volumes = [base + 1 if index < remainder else base for index in range(len(days))]

    for day, test_volume in zip(days, schedule_volumes):
        scheduled_at = get_due_date(poured_at, day)
        await create_test_schedule(db, batch_id, day, test_volume, scheduled_at)

    tests_lines = "\n".join([f"{d} {t(language, 'days_label')} — {schedule_volumes[i]} м³" for i, d in enumerate(days)])
    await safe_edit_text(
        query,
        t(language, "batch_created") + "\n"
        f"{t(language, 'grade_label', grade=grade)}\n"
        f"{t(language, 'picket_label', picket=picket)}\n"
        f"{t(language, 'poured_label', poured_at=format_date(poured_at))}\n"
        f"{t(language, 'volume_total', total_volume=int(volume))}\n\n"
        f"{t(language, 'test_plan_title')}\n{tests_lines}",
        reply_markup=main_menu_keyboard(language),
    )
    await state.clear()


@router.callback_query(lambda query: query.data == "cancel")
async def cancel_callback(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    language = await _get_language(query)
    await query.answer(t(language, "use_main_menu"))
    await safe_edit_text(
        query,
        t(language, "use_main_menu"),
        reply_markup=main_menu_keyboard(language),
    )


def register_concrete_add_handlers(dp) -> None:
    dp.include_router(router)
