from aiogram.fsm.state import StatesGroup, State


class ConcreteStates(StatesGroup):
    date = State()
    grade = State()
    location = State()
    picket = State()
    volume = State()
    tests = State()
    awaiting_test_volume = State()
