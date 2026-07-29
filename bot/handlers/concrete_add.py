from datetime import date
from aiogram import Router
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.database as db_module
from bot.database.queries import (
    create_batch,
    create_test_schedule,
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

router = Router()


@router.callback_query(lambda query: query.data == "concrete_add")
async def start_add_callback(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.answer()
    await query.message.edit_text(
        "📅 Дата заливки\n\n"
        "Выберите дату заливки или введите свою дату в формате дд.мм.гггг.",
        reply_markup=date_keyboard(),
    )
    await state.set_state(ConcreteStates.date)


@router.callback_query(lambda query: query.data == "date_today", StateFilter(ConcreteStates.date))
async def choose_today_callback(query: CallbackQuery, state: FSMContext) -> None:
    poured_at = date.today().isoformat()
    await state.update_data(poured_at=poured_at)
    await query.answer("Сегодняшняя дата выбрана")
    await query.message.edit_text(
        "🧱 Марка бетона\n\n"
        "Выберите марку бетона.",
        reply_markup=grade_keyboard(),
    )
    await state.set_state(ConcreteStates.grade)


@router.message(ConcreteStates.date)
async def enter_date_handler(message: Message, state: FSMContext) -> None:
    poured_at = normalize_date(message.text)
    if poured_at is None:
        await message.answer(
            "Неверный формат даты. Введите дату в формате дд.мм.гггг или нажмите кнопку Сегодня.",
            reply_markup=date_keyboard(),
        )
        return
    await state.update_data(poured_at=poured_at)
    await message.answer(
        "🧱 Марка бетона\n\n"
        "Выберите марку бетона.",
        reply_markup=grade_keyboard(),
    )
    await state.set_state(ConcreteStates.grade)


@router.callback_query(lambda query: query.data.startswith("grade_"), StateFilter(ConcreteStates.grade))
async def choose_grade_callback(query: CallbackQuery, state: FSMContext) -> None:
    grade = query.data.replace("grade_", "")
    await state.update_data(grade=grade)
    await query.answer(f"Марка выбрана: {grade}")
    await query.message.edit_text(
        "📍 Куда идёт бетон?\n\n"
        "Введите локацию или объект.",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ConcreteStates.location)


@router.message(ConcreteStates.location)
async def enter_location_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(location=message.text.strip())
    await message.answer(
        "🏷️ Пикетаж\n\n"
        "Введите пикетаж.",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ConcreteStates.picket)


@router.message(ConcreteStates.picket)
async def enter_picket_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(picket=message.text.strip())
    await message.answer(
        "📦 Объём\n\n"
        "Выберите объём бетонной партии.",
        reply_markup=volume_keyboard(),
    )
    await state.set_state(ConcreteStates.volume)


@router.callback_query(lambda query: query.data.startswith("volume_"), StateFilter(ConcreteStates.volume))
async def choose_volume_callback(query: CallbackQuery, state: FSMContext) -> None:
    volume = float(query.data.replace("volume_", ""))
    await state.update_data(volume=volume)
    await query.answer(f"Объём выбран: {int(volume)} м³")

    await query.message.edit_text(
        "🧪 Выберите дни испытаний\n\n"
        "Нажмите на дни, которые нужно включить. По умолчанию выбраны 7 и 28.",
        reply_markup=tests_keyboard({7, 28}),
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
    await query.answer(f"Выбрано: {sorted(selected)}")
    await query.message.edit_text(
        "🧪 Выберите дни испытаний\n\n"
        "Нажмите на дни, которые нужно включить.",
        reply_markup=tests_keyboard(selected),
    )


@router.callback_query(lambda query: query.data == "tests_confirm", StateFilter(ConcreteStates.tests))
async def confirm_tests_callback(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("tests"):
        await query.answer("Выберите хотя бы один день.", show_alert=True)
        return

    db = db_module.db
    if db is None or query.from_user is None:
        await query.answer("Ошибка базы данных.", show_alert=True)
        return

    poured_at = data["poured_at"]
    grade = data["grade"]
    location = data["location"]
    picket = data["picket"]
    volume = data["volume"]
    days = sorted(data["tests"])

    user_id_row = await db.fetchone("SELECT id FROM users WHERE telegram_id = ?", (query.from_user.id,))
    if user_id_row is None:
        await query.answer("Пользователь не найден.", show_alert=True)
        return

    user_id = user_id_row[0]
    batch_id = await create_batch(db, user_id, grade, location, picket, volume, poured_at, set(days))

    base = int(volume) // len(days)
    remainder = int(volume) % len(days)
    schedule_volumes = [base + 1 if index < remainder else base for index in range(len(days))]

    for day, test_volume in zip(days, schedule_volumes):
        scheduled_at = get_due_date(poured_at, day)
        await create_test_schedule(db, batch_id, day, test_volume, scheduled_at)

    tests_lines = "\n".join([f"{d} дн. — {schedule_volumes[i]} м³" for i, d in enumerate(days)])
    await query.message.edit_text(
        f"✅ Партия создана.\n"
        f"Марка: {grade}\n"
        f"Пикетаж: {picket}\n"
        f"Дата заливки: {format_date(poured_at)}\n"
        f"Объём: {volume} м³\n\n"
        f"Планы испытаний:\n{tests_lines}",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.callback_query(lambda query: query.data == "cancel")
async def cancel_callback(query: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.answer("Добавление отменено")
    await query.message.edit_text(
        "Отмена. Используйте главное меню.",
        reply_markup=main_menu_keyboard(),
    )


def register_concrete_add_handlers(dp) -> None:
    dp.include_router(router)
