from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import main_menu

router = Router()

HELP_TEXT = (
    "👋 Привет! Это бот с отзывами о преподавателях.\n\n"
    "• <b>Найти преподавателя</b> — карточка препода: дисциплины, средние "
    "оценки и отзывы студентов.\n"
    "• <b>Найти дисциплину</b> — кто ведёт предмет и как принимает экзамен.\n"
    "• <b>Оставить отзыв</b> — расскажи, как проходит экзамен, насколько "
    "лоялен препод и насколько понятно объясняет.\n\n"
    "Отзывы проходят автоматическую проверку: мат и спам блокируются, "
    "сомнительные отзывы проверяет модератор.\n"
    "Команда /cancel отменяет текущее действие."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нечего отменять 🙂", reply_markup=main_menu())
        return
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu())


@router.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer(
        "Не понял сообщение. Выбери действие в меню или напиши /help.",
        reply_markup=main_menu(),
    )
