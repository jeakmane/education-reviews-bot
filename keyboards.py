from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Найти преподавателя")
    kb.button(text="📚 Найти дисциплину")
    kb.button(text="✍️ Оставить отзыв")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)


def teachers_keyboard(teachers: list[tuple[int, str]], prefix: str) -> InlineKeyboardMarkup:
    """Список преподавателей. prefix: 'teacher' (просмотр) или 'rev_teacher' (отзыв)."""
    kb = InlineKeyboardBuilder()
    for teacher_id, name in teachers:
        kb.button(text=name, callback_data=f"{prefix}:{teacher_id}")
    kb.adjust(1)
    return kb.as_markup()


def disciplines_keyboard(disciplines: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for discipline_id, name in disciplines:
        kb.button(text=name, callback_data=f"disc:{discipline_id}")
    kb.adjust(1)
    return kb.as_markup()


def rating_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Оценка 1–5. prefix: 'rev_loyalty', 'rev_difficulty', 'rev_clarity'."""
    kb = InlineKeyboardBuilder()
    for i in range(1, 6):
        kb.button(text="⭐" * i, callback_data=f"{prefix}:{i}")
    kb.adjust(5)
    return kb.as_markup()


def reviews_nav_keyboard(teacher_id: int, page: int, has_next: bool) -> InlineKeyboardMarkup | None:
    if page == 0 and not has_next:
        return None
    kb = InlineKeyboardBuilder()
    if page > 0:
        kb.button(text="⬅️ Назад", callback_data=f"page:{teacher_id}:{page - 1}")
    if has_next:
        kb.button(text="➡️ Дальше", callback_data=f"page:{teacher_id}:{page + 1}")
    kb.adjust(2)
    return kb.as_markup()


def moderation_keyboard(review_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Одобрить", callback_data=f"mod:approve:{review_id}")
    kb.button(text="❌ Отклонить", callback_data=f"mod:reject:{review_id}")
    kb.adjust(2)
    return kb.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить преподавателя", callback_data="admin:add_teacher")
    kb.button(text="➕ Добавить дисциплину", callback_data="admin:add_discipline")
    kb.button(text="📝 На модерации", callback_data="admin:pending")
    kb.button(text="📊 Статистика", callback_data="admin:stats")
    kb.adjust(1)
    return kb.as_markup()
