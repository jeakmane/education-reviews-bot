from aiogram.fsm.state import State, StatesGroup


class SearchTeacher(StatesGroup):
    query = State()


class SearchDiscipline(StatesGroup):
    query = State()


class ReviewForm(StatesGroup):
    teacher = State()
    loyalty = State()
    difficulty = State()
    clarity = State()
    text = State()


class AddTeacher(StatesGroup):
    name = State()
    disciplines = State()


class AddDiscipline(StatesGroup):
    name = State()
