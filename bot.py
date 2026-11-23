import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config_error
from db import init_db
from handlers import register_routers


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    error = config_error()
    if error:
        raise SystemExit(error)

    from config import BOT_TOKEN, PROXY_URL

    await init_db()

    session = None
    if PROXY_URL:
        from aiogram.client.session.aiohttp import AiohttpSession

        session = AiohttpSession(proxy=PROXY_URL)
        logging.getLogger(__name__).info("Используется прокси: %s", PROXY_URL)

    bot = Bot(
        BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    register_routers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
