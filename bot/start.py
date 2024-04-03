import asyncio
import os

import django
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from django.db.migrations import executor
from dotenv import load_dotenv


async def start():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

    django.setup()

    from handlers.basic import basic_router
    load_dotenv()

    bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties())

    dp = Dispatcher()
    dp.include_router(basic_router)


    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(start())
