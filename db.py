"""Работа с базой данных SQLite (через aiosqlite)."""

from datetime import datetime, timezone

import aiosqlite

from config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    search_name TEXT NOT NULL,  -- lower(): SQLite LIKE не работает с кириллицей
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS disciplines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    search_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teacher_disciplines (
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    discipline_id INTEGER NOT NULL REFERENCES disciplines(id) ON DELETE CASCADE,
    PRIMARY KEY (teacher_id, discipline_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    username TEXT,
    loyalty INTEGER NOT NULL CHECK (loyalty BETWEEN 1 AND 5),
    difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    clarity INTEGER NOT NULL CHECK (clarity BETWEEN 1 AND 5),
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_teacher ON reviews(teacher_id, status);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id, created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


# ---------- Преподаватели и дисциплины ----------

async def add_teacher(full_name: str) -> int | None:
    """Возвращает id преподавателя или None, если уже существует."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cur = await db.execute(
                "INSERT INTO teachers (full_name, search_name, created_at) "
                "VALUES (?, ?, ?)",
                (full_name.strip(), full_name.strip().lower(), _now()),
            )
            await db.commit()
            return cur.lastrowid
        except aiosqlite.IntegrityError:
            return None


async def add_discipline(name: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cur = await db.execute(
                "INSERT INTO disciplines (name, search_name) VALUES (?, ?)",
                (name.strip(), name.strip().lower()),
            )
            await db.commit()
            return cur.lastrowid
        except aiosqlite.IntegrityError:
            return None


async def link_teacher_discipline(teacher_id: int, discipline_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO teacher_disciplines (teacher_id, discipline_id) "
            "VALUES (?, ?)",
            (teacher_id, discipline_id),
        )
        await db.commit()


async def search_teachers(query: str, limit: int = 10) -> list[tuple[int, str]]:
    pattern = f"%{query.strip().lower()}%"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, full_name FROM teachers WHERE search_name LIKE ? "
            "ORDER BY full_name LIMIT ?",
            (pattern, limit),
        )
        return await cur.fetchall()


async def search_disciplines(query: str, limit: int = 10) -> list[tuple[int, str]]:
    pattern = f"%{query.strip().lower()}%"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, name FROM disciplines WHERE search_name LIKE ? "
            "ORDER BY name LIMIT ?",
            (pattern, limit),
        )
        return await cur.fetchall()


async def teachers_by_discipline(discipline_id: int) -> list[tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT t.id, t.full_name FROM teachers t "
            "JOIN teacher_disciplines td ON td.teacher_id = t.id "
            "WHERE td.discipline_id = ? ORDER BY t.full_name",
            (discipline_id,),
        )
        return await cur.fetchall()


async def get_teacher(teacher_id: int) -> tuple[int, str] | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, full_name FROM teachers WHERE id = ?", (teacher_id,)
        )
        return await cur.fetchone()


async def teacher_disciplines(teacher_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT d.name FROM disciplines d "
            "JOIN teacher_disciplines td ON td.discipline_id = d.id "
            "WHERE td.teacher_id = ? ORDER BY d.name",
            (teacher_id,),
        )
        return [row[0] for row in await cur.fetchall()]


# ---------- Отзывы ----------

async def teacher_stats(teacher_id: int) -> dict:
    """Средние оценки и число одобренных отзывов."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*), AVG(loyalty), AVG(difficulty), AVG(clarity), "
            "AVG((loyalty + clarity + (6 - difficulty)) / 3.0) "
            "FROM reviews WHERE teacher_id = ? AND status = 'approved'",
            (teacher_id,),
        )
        count, loyalty, difficulty, clarity, overall = await cur.fetchone()
    return {
        "count": count,
        "loyalty": round(loyalty, 1) if loyalty else None,
        "difficulty": round(difficulty, 1) if difficulty else None,
        "clarity": round(clarity, 1) if clarity else None,
        "overall": round(overall, 1) if overall else None,
    }


async def approved_reviews(
    teacher_id: int, offset: int = 0, limit: int = 3
) -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT loyalty, difficulty, clarity, text FROM reviews "
            "WHERE teacher_id = ? AND status = 'approved' "
            "ORDER BY id DESC LIMIT ? OFFSET ?",
            (teacher_id, limit, offset),
        )
        return await cur.fetchall()


async def count_user_reviews_today(user_id: int) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND created_at >= ?",
            (user_id, today),
        )
        (count,) = await cur.fetchone()
        return count


async def create_review(
    teacher_id: int,
    user_id: int,
    username: str | None,
    loyalty: int,
    difficulty: int,
    clarity: int,
    text: str,
    status: str,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO reviews "
            "(teacher_id, user_id, username, loyalty, difficulty, clarity, "
            " text, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (teacher_id, user_id, username, loyalty, difficulty, clarity,
             text, status, _now()),
        )
        await db.commit()
        return cur.lastrowid


async def set_review_status(review_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reviews SET status = ? WHERE id = ?", (status, review_id)
        )
        await db.commit()


async def get_review(review_id: int) -> tuple | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT r.id, r.user_id, t.full_name, r.loyalty, r.difficulty, "
            "r.clarity, r.text, r.status FROM reviews r "
            "JOIN teachers t ON t.id = r.teacher_id WHERE r.id = ?",
            (review_id,),
        )
        return await cur.fetchone()


async def pending_reviews() -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT r.id, t.full_name, r.text FROM reviews r "
            "JOIN teachers t ON t.id = r.teacher_id "
            "WHERE r.status = 'pending' ORDER BY r.id"
        )
        return await cur.fetchall()


async def stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        result = {}
        for key, sql in (
            ("teachers", "SELECT COUNT(*) FROM teachers"),
            ("disciplines", "SELECT COUNT(*) FROM disciplines"),
            ("approved", "SELECT COUNT(*) FROM reviews WHERE status='approved'"),
            ("pending", "SELECT COUNT(*) FROM reviews WHERE status='pending'"),
        ):
            cur = await db.execute(sql)
            (result[key],) = await cur.fetchone()
        return result
