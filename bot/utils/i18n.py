from typing import Any

DEFAULT_LANGUAGE = "ru"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "welcome_greeting": "Добро пожаловать 👋",
        "choose_action": "Выберите действие:",
        "main_menu_title": "Добро пожаловать 👋\nВыберите действие:",
        "list_concrete_button": "📋 Список бетона",
        "add_concrete_button": "➕ Добавить бетон",
        "settings_button": "⚙️ Настройки",
        "main_menu_button": "Главное меню",
        "today_button": "Сегодня",
        "today_selected": "Сегодня выбрана",
        "selected_days": "Выбрано: {days}",
        "cancel_button": "Отмена",
        "done_button": "Готово",
        "choose_date": "📅 Дата заливки\n\nВыберите дату заливки или введите свою дату в формате дд.мм.гггг.",
        "choose_grade": "🧱 Марка бетона\n\nВыберите марку бетона.",
        "enter_location": "📍 Куда идёт бетон?\n\nВведите локацию или объект.",
        "enter_picket": "🏷️ Пикетаж\n\nВведите пикетаж.",
        "choose_volume": "📦 Объём\n\nВыберите объём бетонной партии.",
        "volume_3": "3 кубика",   
        "volume_6": "6 кубиков",   
        "volume_12": "12 кубиков", 
        "choose_test_days": "🧪 Выберите дни испытаний\n\nНажмите на дни, которые нужно включить.",
        "choose_test_days_default": "🧪 Выберите дни испытаний\n\nНажмите на дни, которые нужно включить. По умолчанию выбраны 7 и 28.",
        "batch_created": "✅ Партия создана.",
        "use_main_menu": "Отмена. Используйте главное меню.",
        "invalid_date": "Неверный формат даты. Введите дату в формате дд.мм.гггг или нажмите кнопку Сегодня.",
        "db_error": "Ошибка базы данных.",
        "user_not_found": "Пользователь не найден.",
        "concrete_list_title": "📋 Список бетона\n\n",
        "no_batches": "Пока нет ни одной партии. Нажмите Добавить бетон.",
        "settings_title": "⚙️ Настройки",
        "choose_language": "Выберите язык:",
        "language_ru": "Русский",
        "language_en": "English",
        "language_selected": "Язык установлен: {language_name}",
        "back": "◀️ Назад",
        "confirm_test": "✅ Подтвердить",
        "confirm_cancel": "❌ Отмена",
        "test_confirmation": "🧪 ПОДТВЕРЖДЕНИЕ ИСПЫТАНИЯ\n\n",
        "waiting_status": "⏳ ожидает",
        "done_status": "✅ выполнено",
        "tests_complete": "✅ ИСПЫТАНИЯ ЗАВЕРШЕНЫ",
        "batch_label": "🧱 БЕТОН #{id}",
        "grade_label": "Марка: {grade}",
        "location_label": "📍 Объект: {location}",
        "picket_label": "🏷️ Пикетаж: {picket}",
        "poured_label": "📅 Дата заливки: {poured_at}",
        "volume_total": "Всего кубиков: {total_volume}",
        "volume_tested": "Испытано: {tested}",
        "volume_remaining": "Осталось: {remaining}",
        "test_plan_title": "🧪 ПЛАН ИСПЫТАНИЙ",
        "test_line": "{days} дней — {volume} кубика — {status}",
        "perform_test_button": "🧪 Выполнить испытание {days}д — {volume} кубика",
        "days_label": "дн.",
        "language_setting_title": "Язык",
        "language_setting_value": "Язык: {language}",
        "plan_empty": "План испытаний пока пуст.",
        "confirm_completion": "Подтвердить выполнение?",
        "setting_updated": "Настройка испытаний обновлена.",
        "batch_not_found": "Партия не найдена.",
        "invalid_batch_id": "Неверный идентификатор партии.",
        "invalid_id": "Неверный идентификатор.",
        "test_not_found": "Испытание не найдено.",
        "test_confirmed": "Испытание подтверждено.",
        "cancelled": "Отменено.",
        "tests_today_title": "🧪 ИСПЫТАНИЯ НА СЕГОДНЯ",
        "open_batch_button": "🧪 Открыть бетон",
        "notify_day": "{days} дней {status}",
    },
    "en": {
        "welcome_greeting": "Welcome 👋",
        "choose_action": "Choose an action:",
        "main_menu_title": "Welcome 👋\nChoose an action:",
        "list_concrete_button": "📋 Concrete list",
        "add_concrete_button": "➕ Add concrete",
        "settings_button": "⚙️ Settings",
        "main_menu_button": "Main menu",
        "today_button": "Today",
        "today_selected": "Today selected",
        "selected_days": "Selected: {days}",
        "cancel_button": "Cancel",
        "done_button": "Done",
        "choose_date": "📅 Pour date\n\nChoose a pour date or enter your own in dd.mm.yyyy format.",
        "choose_grade": "🧱 Concrete grade\n\nChoose a concrete grade.",
        "enter_location": "📍 Where is the concrete going?\n\nEnter a location or site.",
        "enter_picket": "🏷️ Picket\n\nEnter the picket.",
        "choose_volume": "📦 Volume\n\nChoose the batch volume.",
        "volume_3": "3 cubes",
        "volume_6": "6 cubes",
        "volume_12": "12 cubes",
        "choose_test_days": "🧪 Choose test days\n\nTap the days you want to include.",
        "choose_test_days_default": "🧪 Choose test days\n\nTap the days you want to include. Defaults are 7 and 28.",
        "batch_created": "✅ Batch created.",
        "use_main_menu": "Canceled. Use the main menu.",
        "invalid_date": "Invalid date format. Enter date as dd.mm.yyyy or press Today.",
        "db_error": "Database error.",
        "user_not_found": "User not found.",
        "concrete_list_title": "📋 Concrete list\n\n",
        "no_batches": "No batches yet. Press Add concrete.",
        "settings_title": "⚙️ Settings",
        "choose_language": "Choose language:",
        "language_ru": "Русский",
        "language_en": "English",
        "language_selected": "Language set: {language_name}",
        "back": "◀️ Back",
        "confirm_test": "✅ Confirm",
        "confirm_cancel": "❌ Cancel",
        "test_confirmation": "🧪 TEST CONFIRMATION\n\n",
        "waiting_status": "⏳ waiting",
        "done_status": "✅ completed",
        "tests_complete": "✅ TESTS COMPLETE",
        "batch_label": "🧱 CONCRETE #{id}",
        "grade_label": "Grade: {grade}",
        "location_label": "📍 Location: {location}",
        "picket_label": "🏷️ Picket: {picket}",
        "poured_label": "📅 Pour date: {poured_at}",
        "volume_total": "Total cubes: {total_volume}",
        "volume_tested": "Tested: {tested}",
        "volume_remaining": "Remaining: {remaining}",
        "test_plan_title": "🧪 TEST PLAN",
        "test_line": "{days} days — {volume} cubes — {status}",
        "perform_test_button": "🧪 Perform {days}d test — {volume} cubes",
        "days_label": "d",
        "language_setting_title": "Language",
        "language_setting_value": "Language: {language}",
        "select_at_least_one_day": "Choose at least one day.",
        "plan_empty": "The test plan is empty.",
        "confirm_completion": "Confirm completion?",
        "setting_updated": "Test settings updated.",
        "batch_not_found": "Batch not found.",
        "invalid_batch_id": "Invalid batch identifier.",
        "invalid_id": "Invalid identifier.",
        "test_not_found": "Test not found.",
        "test_confirmed": "Test confirmed.",
        "cancelled": "Cancelled.",
        "tests_today_title": "🧪 TESTS TODAY",
        "open_batch_button": "🧪 Open batch",
        "notify_day": "{days} days {status}",
    },
}


def detect_language(language_code: str | None) -> str:
    if not language_code:
        return DEFAULT_LANGUAGE
    normalized = language_code.lower()
    if normalized.startswith("en"):
        return "en"
    if normalized.startswith("ru"):
        return "ru"
    return DEFAULT_LANGUAGE


def t(language: str, key: str, **kwargs: Any) -> str:
    translations = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = translations.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**kwargs)


from bot.database.queries import get_user_by_telegram


async def get_user_language(db, telegram_id: int) -> str:
    user = await get_user_by_telegram(db, telegram_id)
    if user and user.get("language"):
        return user["language"]
    return DEFAULT_LANGUAGE

