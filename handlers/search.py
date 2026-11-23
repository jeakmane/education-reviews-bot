from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from config import REVIEWS_PAGE_SIZE
from keyboards import (
    disciplines_keyboard,
    reviews_nav_keyboard,
    teachers_keyboard,
)
from states import SearchDiscipline, SearchTeacher

router = Router()


def format_teacher_card(
    name: str, disciplines: list[str], stats: dict, reviews: list[tuple], page: int
) -> str:
    lines = [f"👤 <b>{escape(name)}</b>"]
    lines.append(
        "📚 Дисциплины: " + (", ".join(escape(d) for d in disciplines) or "не указаны")
    )
    if stats["count"]:
        lines.append(
            f"⭐ Общая оценка: <b>{stats['overall']}</b>/5 "
            f"({stats['count']} отзывов)\n"
            f"   Лояльность: {stats['loyalty']} | "
            f"Сложность экзамена: {stats['difficulty']} | "
            f"Понятность: {stats['clarity']}"
        )
    else:
        lines.append("Отзывов пока нет — стань первым! (кнопка «✍️ Оставить отзыв»)")

    if reviews:
        lines.append(f"\n<b>Отзывы (стр. {page + 1}):</b>")
        start = page * REVIEWS_PAGE_SIZE
        for i, (loyalty, difficulty, clarity, text) in enumerate(reviews, start + 1):
            overall = round((loyalty + clarity + (6 - difficulty)) / 3, 1)
            lines.append(f"{i}) ⭐{overall} — «{escape(text)}»")
    return "\n".join(lines)


async def show_teacher_card(target, teacher_id: int, page: int, edit: bool) -> None:
    teacher = await db.get_teacher(teacher_id)
    if not teacher:
        return
    _, name = teacher
    disciplines = await db.teacher_disciplines(teacher_id)
    stats = await db.teacher_stats(teacher_id)
    reviews = await db.approved_reviews(
        teacher_id, offset=page * REVIEWS_PAGE_SIZE, limit=REVIEWS_PAGE_SIZE
    )
    has_next = len(
        await db.approved_reviews(
            teacher_id, offset=(page + 1) * REVIEWS_PAGE_SIZE, limit=1
        )
    ) > 0
    text = format_teacher_card(name, disciplines, stats, reviews, page)
    keyboard = reviews_nav_keyboard(teacher_id, page, has_next)
    if edit:
        await target.message.edit_text(text, reply_markup=keyboard)
    else:
        await target.message.answer(text, reply_markup=keyboard)


# ---------- Поиск преподавателя ----------

@router.message(F.text == "🔍 Найти преподавателя")
async def find_teacher(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchTeacher.query)
    await message.answer("Введи фамилию или имя преподавателя:")


@router.message(SearchTeacher.query)
async def find_teacher_results(message: Message, state: FSMContext) -> None:
    await state.clear()
    teachers = await db.search_teachers(message.text)
    if not teachers:
        await message.answer(
            "Никого не нашёл 🤷 Попробуй другую формулировку "
            "(например, только фамилию)."
        )
        return
    await message.answer(
        "Найденные преподаватели:", reply_markup=teachers_keyboard(teachers, "teacher")
    )


@router.callback_query(F.data.startswith("teacher:"))
async def teacher_card(callback: CallbackQuery) -> None:
    teacher_id = int(callback.data.split(":")[1])
    await show_teacher_card(callback, teacher_id, page=0, edit=False)
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def reviews_page(callback: CallbackQuery) -> None:
    _, teacher_id, page = callback.data.split(":")
    await show_teacher_card(callback, int(teacher_id), int(page), edit=True)
    await callback.answer()


# ---------- Поиск дисциплины ----------

@router.message(F.text == "📚 Найти дисциплину")
async def find_discipline(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchDiscipline.query)
    await message.answer("Введи название дисциплины:")


@router.message(SearchDiscipline.query)
async def find_discipline_results(message: Message, state: FSMContext) -> None:
    await state.clear()
    disciplines = await db.search_disciplines(message.text)
    if not disciplines:
        await message.answer("Такой дисциплины не нашёл 🤷 Попробуй иначе.")
        return
    await message.answer(
        "Найденные дисциплины:", reply_markup=disciplines_keyboard(disciplines)
    )


@router.callback_query(F.data.startswith("disc:"))
async def discipline_teachers(callback: CallbackQuery) -> None:
    discipline_id = int(callback.data.split(":")[1])
    teachers = await db.teachers_by_discipline(discipline_id)
    if not teachers:
        await callback.message.answer("По этой дисциплине преподаватели не указаны.")
    else:
        await callback.message.answer(
            "Кто ведёт эту дисциплину:",
            reply_markup=teachers_keyboard(teachers, "teacher"),
        )
    await callback.answer()
