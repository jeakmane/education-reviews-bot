from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from config import ADMIN_IDS
from keyboards import admin_menu, moderation_keyboard
from states import AddDiscipline, AddTeacher

router = Router()

router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🛠 Панель администратора:", reply_markup=admin_menu())


# ---------- Добавление преподавателя ----------

@router.callback_query(F.data == "admin:add_teacher")
async def add_teacher_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddTeacher.name)
    await callback.message.answer("Введите ФИО преподавателя:")
    await callback.answer()


@router.message(AddTeacher.name)
async def add_teacher_name(message: Message, state: FSMContext) -> None:
    teacher_id = await db.add_teacher(message.text)
    if teacher_id is None:
        await message.answer("Такой преподаватель уже есть. Введите другое ФИО или /cancel.")
        return
    await state.update_data(teacher_id=teacher_id, teacher_name=message.text.strip())
    await state.set_state(AddTeacher.disciplines)
    await message.answer(
        "Введите дисциплины через запятую (или «-», если без дисциплин):"
    )


@router.message(AddTeacher.disciplines)
async def add_teacher_disciplines(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    added = []
    if message.text.strip() != "-":
        for name in message.text.split(","):
            name = name.strip()
            if not name:
                continue
            discipline_id = await db.add_discipline(name)
            if discipline_id is None:
                # дисциплина уже есть — найдём её id
                found = await db.search_disciplines(name, limit=50)
                discipline_id = next(
                    (d_id for d_id, d_name in found if d_name.lower() == name.lower()),
                    None,
                )
            if discipline_id is not None:
                await db.link_teacher_discipline(data["teacher_id"], discipline_id)
                added.append(name)
    await message.answer(
        f"✅ Преподаватель <b>{escape(data['teacher_name'])}</b> добавлен."
        + (f"\nДисциплины: {escape(', '.join(added))}" if added else ""),
        reply_markup=admin_menu(),
    )


# ---------- Добавление дисциплины ----------

@router.callback_query(F.data == "admin:add_discipline")
async def add_discipline_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddDiscipline.name)
    await callback.message.answer("Введите название дисциплины:")
    await callback.answer()


@router.message(AddDiscipline.name)
async def add_discipline_name(message: Message, state: FSMContext) -> None:
    await state.clear()
    if await db.add_discipline(message.text) is None:
        await message.answer("Такая дисциплина уже есть.", reply_markup=admin_menu())
    else:
        await message.answer(
            f"✅ Дисциплина <b>{escape(message.text.strip())}</b> добавлена.",
            reply_markup=admin_menu(),
        )


# ---------- Модерация ----------

async def send_pending(target_message: Message) -> None:
    pending = await db.pending_reviews()
    if not pending:
        await target_message.answer("Очередь модерации пуста ✅", reply_markup=admin_menu())
        return
    await target_message.answer(f"Отзывов на модерации: {len(pending)}")
    for review_id, teacher_name, text in pending[:10]:
        review = await db.get_review(review_id)
        _, _, _, loyalty, difficulty, clarity, full_text, _ = review
        await target_message.answer(
            f"#{review_id} • <b>{escape(teacher_name)}</b>\n"
            f"Лояльность {loyalty} | Сложность {difficulty} | Понятность {clarity}\n\n"
            f"«{escape(full_text)}»",
            reply_markup=moderation_keyboard(review_id),
        )


@router.callback_query(F.data == "admin:pending")
async def pending_list(callback: CallbackQuery) -> None:
    await send_pending(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("mod:"))
async def moderate_review(callback: CallbackQuery, bot: Bot) -> None:
    _, action, review_id = callback.data.split(":")
    review = await db.get_review(int(review_id))
    if not review or review[7] != "pending":
        await callback.answer("Отзыв уже обработан", show_alert=True)
        return
    _, user_id, teacher_name, *_ = review
    if action == "approve":
        await db.set_review_status(int(review_id), "approved")
        await callback.message.edit_text(callback.message.text + "\n\n✅ Одобрено")
        try:
            await bot.send_message(
                user_id,
                f"✅ Твой отзыв о <b>{escape(teacher_name)}</b> прошёл модерацию и опубликован!",
            )
        except Exception:
            pass
    else:
        await db.set_review_status(int(review_id), "rejected")
        await callback.message.edit_text(callback.message.text + "\n\n❌ Отклонено")
        try:
            await bot.send_message(
                user_id,
                f"❌ К сожалению, твой отзыв о <b>{escape(teacher_name)}</b> "
                "не прошёл модерацию.",
            )
        except Exception:
            pass
    await callback.answer()


# ---------- Статистика ----------

@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery) -> None:
    s = await db.stats()
    await callback.message.answer(
        f"📊 <b>Статистика</b>\n"
        f"Преподавателей: {s['teachers']}\n"
        f"Дисциплин: {s['disciplines']}\n"
        f"Опубликовано отзывов: {s['approved']}\n"
        f"На модерации: {s['pending']}",
        reply_markup=admin_menu(),
    )
    await callback.answer()
