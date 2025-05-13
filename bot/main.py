import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import API_TOKEN
from bot.database import update_db_schema, update_payment_table
from bot.handlers import start, order, payment, review, admin

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=API_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация хендлеров
    dp.include_router(start.router)
    dp.include_router(order.router)
    dp.include_router(payment.router)
    dp.include_router(review.router)
    dp.include_router(admin.router)
    
    # Обновление схемы БД
    update_db_schema()
    update_payment_table()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 