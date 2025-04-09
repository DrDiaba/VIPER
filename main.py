import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
import re
from datetime import datetime, timedelta

API_TOKEN = '8174365297:AAGNec-9iRN6YCcVBZk6zWecQHcDcnht7kM'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище таймеров
user_timers = {}

def parse_time_input(text: str):
    """Извлекает название и время из текста"""
    match = re.match(r'(.+)\s+через\s+(\d+)\s*(секунд|минут|час|часов|часы)?', text, re.IGNORECASE)
    if not match:
        return None
    name, amount, unit = match.groups()
    amount = int(amount)
    if not unit or 'секунд' in unit:
        delta = timedelta(seconds=amount)
    elif 'минут' in unit:
        delta = timedelta(minutes=amount)
    elif 'час' in unit:
        delta = timedelta(hours=amount)
    else:
        return None
    return name.strip(), delta

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Привет! Чтобы создать таймер, напиши:\n\n/timer Название через 10 минут")

@dp.message_handler(commands=['timer'])
async def timer_handler(message: types.Message):
    text = message.get_args()
    parsed = parse_time_input(text)
    if not parsed:
        await message.reply("❌ Неверный формат. Пример: /timer Напомнить про чай через 5 минут")
        return

    name, delta = parsed
    due_time = datetime.now() + delta

    # Сохраняем таймер
    user_id = message.from_user.id
    timer_id = f"{user_id}_{name}"
    user_timers[timer_id] = due_time

    await message.reply(f"✅ Таймер \"{name}\" установлен. Я напомню через {delta}.")

    # Ждём и уведомляем
    await asyncio.sleep(delta.total_seconds())
    await bot.send_message(chat_id=user_id, text=f"⏰ Таймер \"{name}\" завершён!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
