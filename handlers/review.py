from html import escape

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
from config import ADMIN_IDS, MAX_REVIEWS_PER_DAY
from keyboards import moderation_keyboard, rating_keyboard, teachers_keyboard
from moderation import moderate
from states import ReviewForm

router = Router()

RATING_QUESTIONS = {
    "loyalty": (
        "1️⃣ Насколько преподаватель <b>лоялен</b>?\n"
        "(1 — тиран, валит на каждом шагу; 5 — золотой человек)"
    ),
    "difficulty": (
        "2️⃣ Насколько <b>сложно сдать</b> экзамен/зачёт?\n"
        "(1 — халява; 5 — почти невозможно)"
    ),
    "clarity": (
        "3️⃣ Насколько <b>понятно объясняет</b> материал?\n"
        "(1 — ничего не ясно; 5 — объясняет отлично)"
    ),
}


@router.message(F.text == "✍️ Оставить отзыв")
async def start_review(message: Message, state: FSMContext) -> None:
    await state.set_state(ReviewForm.teacher)
    await message.answer(
        "Введи фамилию преподавателя, о котором хочешь оставить отзыв:"
    )


@router.message(ReviewForm.teacher)
async def review_find_teacher(message: Message, state: FSMContext) -> None:
    teachers = await db.search_teachers(message.text)
    if not teachers:
        await message.answer(
            "Такого преподавателя нет в базе 🤷\n"
            "Попробуй ещё раз или напиши /cancel.\n"
            "Если препода точно нет — попроси админа добавить его."
        )
        return
    await message.answer(
        "Выбери преподавателя:", reply_markup=teachers_keyboard(teachers, "rev_teacher")
    )


@router.callback_query(F.data.startswith("rev_teacher:"))
async def review_choose_teacher(callback: CallbackQuery, state: FSMContext) -> None:
    teacher_id = int(callback.data.split(":")[1])
    teacher = await db.get_teacher(teacher_id)
    if not teacher:
        await callback.answer("Преподаватель не найден", show_alert=True)
        return
    await state.update_data(teacher_id=teacher_id, teacher_name=teacher[1])
    await state.set_state(ReviewForm.loyalty)
    await callback.message.answer(
        f"Оцениваем: <b>{escape(teacher[1])}</b>\n\n" + RATING_QUESTIONS["loyalty"],
        reply_markup=rating_keyboard("rev_loyalty"),
    )
    await callback.answer()


async def _ask_next(callback: CallbackQuery, state: FSMContext, key: str, next_state) -> None:
    await state.set_state(next_state)
    await callback.message.answer(
        RATING_QUESTIONS[key], reply_markup=rating_keyboard(f"rev_{key}")
    )


@router.callback_query(ReviewForm.loyalty, F.data.startswith("rev_loyalty:"))
async def review_loyalty(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(loyalty=int(callback.data.split(":")[1]))
    await _ask_next(callback, state, "difficulty", ReviewForm.difficulty)
    await callback.answer()


@router.callback_query(ReviewForm.difficulty, F.data.startswith("rev_difficulty:"))
async def review_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(difficulty=int(callback.data.split(":")[1]))
    await _ask_next(callback, state, "clarity", ReviewForm.clarity)
    await callback.answer()


@router.callback_query(ReviewForm.clarity, F.data.startswith("rev_clarity:"))
async def review_clarity(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(clarity=int(callback.data.split(":")[1]))
    await state.set_state(ReviewForm.text)
    await callback.message.answer(
        "4️⃣ Теперь напиши <b>текстовый отзыв</b>: как проходит экзамен, "
        "что спрашивает, какие особенности.\n\n"
        "⚠️ Без мата, личных оскорблений и ссылок — такие отзывы не публикуются."
    )
    await callback.answer()


@router.message(ReviewForm.text)
async def review_text(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()

    if await db.count_user_reviews_today(message.from_user.id) >= MAX_REVIEWS_PER_DAY:
        await message.answer(
            f"Ты уже оставил(а) {MAX_REVIEWS_PER_DAY} отзыва за сегодня — "
            "это дневной лимит. Возвращайся завтра 🙂"
        )
        return

    result = moderate(message.text)
    if result.verdict == "reject":
        await message.answer(
            "❌ Отзыв отклонён: обнаружена нецензурная лексика.\n"
            "Можно написать тот же отзыв нормальными словами — "
            "нажми «✍️ Оставить отзыв» ещё раз."
        )
        return

    status = "approved" if result.verdict == "ok" else "pending"
    review_id = await db.create_review(
        teacher_id=data["teacher_id"],
        user_id=message.from_user.id,
        username=message.from_user.username,
        loyalty=data["loyalty"],
        difficulty=data["difficulty"],
        clarity=data["clarity"],
        text=message.text,
        status=status,
    )

    if status == "approved":
        await message.answer(
            f"✅ Спасибо! Твой отзыв о <b>{escape(data['teacher_name'])}</b> опубликован."
        )
    else:
        await message.answer(
            "⏳ Отзыв отправлен на проверку модератору "
            f"(причина: {result.reason}). После одобрения он появится в карточке преподавателя."
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"📝 <b>Отзыв на модерации</b> #{review_id}\n"
                    f"Преподаватель: {escape(data['teacher_name'])}\n"
                    f"Оценки: лояльность {data['loyalty']}, сложность "
                    f"{data['difficulty']}, понятность {data['clarity']}\n"
                    f"Причина: {result.reason}\n\n«{escape(message.text)}»",
                    reply_markup=moderation_keyboard(review_id),
                )
            except Exception:
                pass  # админ мог не запускать бота
