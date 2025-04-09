import logging
import re
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, Update
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
import asyncio

# Токен бота (уже указан напрямую в коде)
API_TOKEN = "7910875433:AAE54qUwJk5l0yP6nqZ_GyE1eIQ2NzKDpAA"

# Логирование
logging.basicConfig(level=logging.INFO)

# Создание бота с настройками по умолчанию
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Хранилище активных таймеров
user_timers = {}

# Функция для парсинга текста и извлечения таймера
def parse_time_input(text: str):
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

    # Асинхронное ожидание и уведомление по истечении таймера
    await asyncio.sleep(delta.total_seconds())
    await bot.send_message(user_id, f"⏰ Время вышло! Таймер <b>{name}</b> завершён!")


# Вебхук для Render
async def handle(request):
    json_data = await request.json()

    # Используем Dispatcher для обработки входящего обновления через вебхук
    update = Update(**json_data)
    await dp.process_update(update)


# Функция для установки webhook
async def set_webhook():
    # Указание URL для вебхука
    webhook_url = "https://viper-5e02.onrender.com/webhook"  # URL твоего Render приложения
    await bot.set_webhook(webhook_url)


# Функция для старта
async def on_start(request):
    return web.Response(text="Bot is running!")


# Шаг для отключения
async def on_shutdown(app):
    await bot.close()


# Основная функция для старта
async def main():
    app = web.Application()

    # Добавление маршрутов
    app.router.add_get("/", on_start)
    app.router.add_post("/webhook", handle)

    # Настройка webhook
    await set_webhook()

    # Запуск веб-сервера
    app.on_shutdown.append(on_shutdown)
    return app


# Эта часть запускает приложение в уже существующем цикле событий
if __name__ == "__main__":
    # Запуск веб-сервера без asyncio.run()
    app = asyncio.get_event_loop().run_until_complete(main())
    web.run_app(app, port=80)
