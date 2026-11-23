# 🤖 Бот отзывов о преподавателях

[![tests](https://github.com/jeakmane/education-reviews-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/jeakmane/education-reviews-bot/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Telegram-бот, где студенты ищут преподавателей и дисциплины и оставляют отзывы:
как проходит экзамен, насколько лоялен препод, насколько понятно объясняет.
Отзывы автоматически фильтруются от мата и спама, сомнительные — уходят
модератору на ручную проверку.

Telegram bot for student reviews of university teachers: search by teacher or
course, rate loyalty/exam difficulty/clarity, automatic profanity & spam
filtering with a manual moderation queue. Built with aiogram 3 and SQLite.

## Стек

- Python 3.11+, [aiogram 3](https://docs.aiogram.dev/), SQLite (aiosqlite)

## Возможности

- 🔍 Поиск преподавателя по фамилии → карточка с дисциплинами, средними
  оценками (лояльность / сложность экзамена / понятность) и отзывами
- 📚 Поиск дисциплины → список преподавателей, которые её ведут
- ✍️ Отзыв: 3 оценки 1–5 + текст
- 🛡 Модерация: мат отклоняется автоматически (учитывается обфускация —
  `xуй`, `з@еб@л`, `сууука`), спам/ссылки/КАПС — в очередь к админу
- 🛠 Админ-панель `/admin`: добавление преподавателей и дисциплин,
  очередь модерации, статистика
- ⏱ Антиспам: не более 3 отзывов в сутки от одного пользователя

## Запуск

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # вписать BOT_TOKEN и ADMIN_IDS
python bot.py
```

1. Создай бота у [@BotFather](https://t.me/BotFather), скопируй токен в `.env`.
2. Свой Telegram ID узнай у [@userinfobot](https://t.me/userinfobot),
   впиши в `ADMIN_IDS`.
3. Запусти бота, напиши ему `/admin` и добавь первых преподавателей.

## Тестовые данные

Заполнить базу примерными преподавателями и отзывами для проверки:

```bash
python seed.py
```

## Тесты

```bash
pytest
```

Тесты проверяют фильтр модерации: мат (в т.ч. обфусцированный) отклоняется,
обычные слова («учеба», «страхует») не дают ложных срабатываний, спам-признаки
уходят в очередь.

## Структура

```
bot.py                — точка входа
config.py             — настройки из .env
db.py                 — SQLite: схема и запросы
moderation.py         — фильтр мата и спама
keyboards.py          — клавиатуры
states.py             — FSM-состояния
handlers/
  common.py           — /start, /help, /cancel
  search.py           — поиск преподавателей и дисциплин
  review.py           — сценарий оставления отзыва
  admin.py            — админ-панель и модерация
seed.py               — наполнение базы тестовыми данными
tests/test_moderation.py
```
