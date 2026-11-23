import os
from pathlib import Path

from dotenv import load_dotenv

# Явно грузим .env из папки проекта (рядом с этим файлом)
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", "education.db")

# Прокси для доступа к api.telegram.org, если он заблокирован провайдером.
# Примеры: http://host:3128, http://user:pass@host:3128, socks5://127.0.0.1:1080
PROXY_URL = os.getenv("PROXY_URL", "").strip() or None
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
}

# Максимум отзывов от одного пользователя в сутки (антиспам)
MAX_REVIEWS_PER_DAY = 3

# Размер страницы при показе отзывов
REVIEWS_PAGE_SIZE = 3


def config_error() -> str | None:
    """Описание проблемы с конфигурацией или None, если всё в порядке."""
    if not BOT_TOKEN or BOT_TOKEN == "123456:ABC-your-token":
        if not ENV_PATH.exists():
            return (
                f"Файл .env не найден ({ENV_PATH}).\n"
                "Создай его по образцу .env.example и впиши BOT_TOKEN."
            )
        return (
            f"В файле {ENV_PATH} не задан реальный BOT_TOKEN.\n"
            "Открой .env и замени значение на токен от @BotFather."
        )
    return None
