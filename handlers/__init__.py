from aiogram import Dispatcher

from . import admin, common, review, search


def register_routers(dp: Dispatcher) -> None:
    # ВАЖНО: common с fallback-заглушкой на любой текст — строго последним,
    # иначе он перехватывает команды/кнопки остальных роутеров.
    dp.include_router(admin.router)
    dp.include_router(search.router)
    dp.include_router(review.router)
    dp.include_router(common.router)
