import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiosqlite

# Конфигурация
API_TOKEN = '5849978203:AAFutW7QmgnkuYglaljG2iwx-rE7IyFkOIs'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ------- База данных -------
async def add_user(username, chat_id):
    """Добавление нового пользователя в базу данных"""
    async with aiosqlite.connect("mydatabase.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (username, chat_id) VALUES (?, ?)", (username, chat_id))
        await db.commit()

async def get_user(chat_id):
    """Получение информации о пользователе по chat_id"""
    async with aiosqlite.connect("mydatabase.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        user = await cursor.fetchone()
        return user

async def get_all_sorts():
    """Получение всех сортов из базы данных"""
    async with aiosqlite.connect("mydatabase.db") as db:
        cursor = await db.execute("SELECT * FROM sorts")
        sorts = await cursor.fetchall()
        return sorts

# ------- Обработчики команд -------

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        await add_user(message.from_user.username, message.from_user.id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Заказать"))
    with open("photos/foto0.jpg", "rb") as photo:
        await bot.send_photo(message.chat.id, photo, caption="Доставка Шишек по острову Панган!", reply_markup=markup)

    # Отображение всех сортов после добавления пользователя
    sorts = await get_all_sorts()
    for sort in sorts:
        with open(sort[4], "rb") as photo:  # sort[4] содержит путь к фото
            caption = f"{sort[1]}\nОписание: {sort[2]}\nЦена: {sort[3]}$"
            await bot.send_photo(message.chat.id, photo, caption=caption)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user = await get_user(message.from_user.id)
    if not user:
        await add_user(message.from_user.username, message.from_user.id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Заказать"))
    with open("photos/foto0.jpg", "rb") as photo:
        await bot.send_photo(message.chat.id, photo, caption="Доставка Шишек по острову Панган!", reply_markup=markup)

# ------- Запуск -------
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
