#!/usr/bin/python
import asyncio
import logging
from queue import Queue

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from bottaxi.config import load_config
from bottaxi.filters.admin import AdminFilter
from bottaxi.handlers.admin import register_admin
from bottaxi.handlers.errors import register_errors_handler
from bottaxi.handlers.user import register_user
from bottaxi.middlewares.database import DatabaseMiddleware
from bottaxi.middlewares.environment import EnvironmentMiddleware
from bottaxi.middlewares.throttling import ThrottlingMiddleware
from bottaxi.models.config import create_session_pool


logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config, session_pool):
    dp.setup_middleware(EnvironmentMiddleware(config=config))
    dp.setup_middleware(DatabaseMiddleware(session=session_pool))
    dp.setup_middleware(ThrottlingMiddleware())


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)
    register_errors_handler(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    storage = RedisStorage2() if config.tg_bot.use_redis else MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    session_pool = await create_session_pool(db=config.db, echo=False)
    queue = Queue()

    bot['config'] = config
    bot['dp'] = dp
    bot['queue'] = queue

    register_all_middlewares(dp, config, session_pool)
    register_all_filters(dp)
    register_all_handlers(dp)

    # start
    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await (await bot.get_session()).close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
    except TimeoutError as e:
        logging.error(f'Возникла ошибка времени ожидания: {e}')
