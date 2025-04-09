import asyncio
import logging
import re
from datetime import datetime, timedelta
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# Получаем токен из переменной окружения (удобно для Render)
API_TOKEN = os.getenv("API_TOKEN")

# Логгирование
logging.basicConfig(level=logging.INFO)

# Создание бота с настройками по умолчанию (parse_mode = HTML)
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Диспетчер и роутер
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Временное хранилище таймеров (в памяти)
user_timers = {}


def parse_time_input(text: str):
    """
    Извлекает название и время из строки.
    Пример: "Пицца через 10 минут"
    """
    match = re.match(r'(.+)\s+через\s+(\d+)\s*(секунд|минут|час(?:ов)?|часа?)?', text, re.IGNORECASE)
    if not match:
        return None
    name, amount, unit = match.groups()
    amount = int(amount)
    unit = unit.lower() if unit else "секунд"
    if "сек" in unit:
        delta = timedelta(seconds=amount)
    elif "мин" in unit:
        delta = timedelta(minutes=amount)
    elif "час" in unit:
        delta = timedelta(hours=amount)
    else:
        return None
    return name.strip(), delta


@router.message(F.text.startswith("/start"))
async def start_handler(message: Message):
    await message.answer("👋 Привет! Я таймер-бот.\nНапиши:\n<code>/timer Название через 5 минут</code>")


@router.message(F.text.startswith("/timer"))
async def timer_handler(message: Message):
    args = message.text[len("/timer "):].strip()
    parsed = parse_time_input(args)

    if not parsed:
        await message.answer("⚠️ Неверный формат.\nПример: /timer Чайник через 5 минут")
        return

    name, delta = parsed
    user_id = message.from_user.id
    timer_id = f"{user_id}_{name}"

    user_timers[timer_id] = datetime.now() + delta
    await message.answer(f"✅ Таймер <b>{name}</b> установлен на {delta}.")

    # Асинхронное ожидание и уведомление
    await asyncio.sleep(delta.total_seconds())
    await bot.send_message(user_id, f"⏰ Время вышло! Таймер <b>{name}</b> завершён!")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
