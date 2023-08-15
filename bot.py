from aiogram import Bot, types
from aiogram.dispatcher import FSMContext, Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.redis import RedisStorage2
import sqlite3
import re

API_TOKEN = '5849978203:AAFutW7QmgnkuYglaljG2iwx-rE7IyFkOIs'
DATABASE = "marihuana.db"

bot = Bot(token=API_TOKEN)
storage = RedisStorage2()
dp = Dispatcher(bot, storage=storage)

class SortOrder(StatesGroup):
    choosing_sort = State()
    waiting_for_grams = State()

# Получение сортов из базы данных, включая ID
async def get_sorts_from_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, photo_path FROM sorts")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Фильтр для обработчика callback-запросов сортов
async def sort_info_filter(callback_query: types.CallbackQuery):
    return callback_query.data.startswith("info_")

@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    # Отправляем приветственное фото
    await message.answer_photo(photo=open('photos/foto0.jpg', 'rb'), caption="Доставка Шишек по острову Панган!")
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(KeyboardButton("Заказать"))
    markup.add(KeyboardButton("Сорта"))  # Добавляем кнопку "Сорта"
    await message.answer("Выберите действие:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == 'Сорта')
async def show_sorts(message: types.Message):
    sorts = await get_sorts_from_db()
    markup = InlineKeyboardMarkup()
    for sort_id, sort_name, _, _ in sorts:
        markup.add(InlineKeyboardButton(text=sort_name, callback_data=f"info_{sort_id}"))
    await message.answer("Выберите сорт для просмотра информации:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == 'Заказать')
async def choose_sort(message: types.Message):
    sorts = await get_sorts_from_db()
    markup = InlineKeyboardMarkup()
    for sort_id, sort_name, _, _ in sorts:
        markup.add(InlineKeyboardButton(text=sort_name, callback_data=sort_name))
    await message.answer("Выберите сорт:", reply_markup=markup)
    await SortOrder.choosing_sort.set()

@dp.callback_query_handler(sort_info_filter)
async def show_sort_info(callback_query: types.CallbackQuery):
    sort_id = int(callback_query.data[5:])
    sorts = await get_sorts_from_db()
    for _id, name, description, _ in sorts:
        if _id == sort_id:
            await bot.answer_callback_query(callback_query.id)
            await bot.send_message(callback_query.from_user.id, f"{name}\nОписание: {description}")
            return

@dp.callback_query_handler(lambda callback_query: not callback_query.data.startswith("info_"), state=SortOrder.choosing_sort)
async def process_sort_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали {callback_query.data}. Сколько грамм?")
    await SortOrder.waiting_for_grams.set()
    await state.update_data(sort=callback_query.data)

@dp.message_handler(lambda message: re.match(r"^\d+$", message.text), state=SortOrder.waiting_for_grams)
async def process_grams(message: types.Message, state: FSMContext):
    grams = int(message.text)
    order_data = await state.get_data()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (customer, sort_order, gramm_order) VALUES (?, ?, ?)", (message.from_user.id, order_data['sort'], grams))
    conn.commit()
    conn.close()
    await message.answer(f"Заказ на {grams} грамм {order_data['sort']} принят!")
    await state.finish()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
