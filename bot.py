import logging
from aioredis import Redis
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv

# Инициализация переменной Redis с None
redis = None

# Загрузка переменных окружения из .env файла
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Основная клавиатура для пользователя
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Посмотреть товары"))

# Клавиатура для выбора действия после добавления товара в корзину
choose_next_action_kb = ReplyKeyboardMarkup(resize_keyboard=True)
choose_next_action_kb.add(KeyboardButton("Добавить еще?"))
choose_next_action_kb.add(KeyboardButton("Оформить заказ"))

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в магазин! Что вы хотите сделать?", reply_markup=main_kb)

# Остальной код остается прежним...

# Теперь, после добавления товара в корзину, пользователь увидит клавиатуру choose_next_action_kb, предлагающую добавить еще товар или перейти к оформлению заказа. Если пользователь решит добавить еще товар, он нажмет кнопку "Добавить еще?", и вы снова покажете ему список товаров.

# Оформление заказа теперь доступно только после добавления товара в корзину. Если пользователь нажмет "Оформить заказ", ему будут предложены два варианта: подтвердить или отменить заказ. Если заказ подтвержден, вы можете очистить корзину этого пользователя и вернуть его к основной клавиатуре. Если заказ отменен, вы также можете вернуть пользователя к основной клавиатуре.


# Обработчик для просмотра товаров
@dp.message_handler(lambda msg: msg.text == "Посмотреть товары")
async def view_products(message: types.Message):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT product_id, name, price FROM products")
        products = await cursor.fetchall()

        if not products:
            await message.answer("Извините, товары отсутствуют!")
            return

        # Создаем InlineKeyboardMarkup
        kb = InlineKeyboardMarkup(row_width=1)
        for product_id, name, price in products:
            # Для каждого товара создаем кнопку с обратным вызовом
            button = InlineKeyboardButton(text=f"{name} - {price}₽", callback_data=f"product_{product_id}")
            kb.add(button)

        await message.answer("Выберите товар:", reply_markup=kb)


# Обработчик нажатия на кнопку
@dp.callback_query_handler(lambda c: c.data.startswith('product_'))
async def process_product_choice(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    await bot.answer_callback_query(callback_query.id)

    # Здесь вы можете сохранить product_id в Redis или выполнить другие действия
    await redis.set(str(callback_query.from_user.id), product_id)
    await bot.send_message(callback_query.from_user.id, f"Сколько грамм? Введите число.")


@dp.message_handler(lambda msg: not msg.text.isdigit() and
                    "Добавить" not in msg.text and
                    "Оформить заказ" not in msg.text and
                    "Подтвердить заказ" not in msg.text and
                    "Отменить заказ" not in msg.text)
async def process_product_name(message: types.Message):
    product_name = message.text

    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT product_id FROM products WHERE LOWER(name)=?", (product_name.lower(),))
        product_id = await cursor.fetchone()

        if not product_id:
            await message.answer("Такого товара нет в наличии!")
            return

        # Сохраняем product_id в Redis для последующего использования
        await redis.set(str(message.from_user.id), product_id[0])
        await message.answer(f"Сколько грамм {product_name}? Введите число.")

@dp.message_handler(lambda message: message.text.isdigit())
async def handle_quantity(message: types.Message):
    quantity = int(message.text)
    user_id = message.from_user.id
    product_id = await redis.get(str(user_id))


    if not product_id:
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
        return

    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("INSERT OR IGNORE INTO cart_items(cart_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
        await cursor.execute("UPDATE cart_items SET quantity=? WHERE cart_id=? AND product_id=?", (quantity, user_id, product_id))
        await db.commit()

    await message.answer(f"Товар добавлен в корзину в количестве {quantity} грамм!", reply_markup=choose_next_action_kb)


# Обработчик для добавления товара в корзину
@dp.message_handler(lambda msg: "Добавить" in msg.text and "в корзину" in msg.text)
async def add_to_cart(message: types.Message):
    # Измененная логика извлечения имени продукта
    product_name = " ".join(message.text.split()[1:-2])

    # Интерактив с базой данных для добавления товара в корзину
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()

        # Используем LOWER() для избежания проблем с регистрозависимостью
        await cursor.execute("SELECT product_id FROM products WHERE LOWER(name)=?", (product_name.lower(),))
        product_id = await cursor.fetchone()

        if not product_id:
            await message.answer("Такого товара нет в наличии!")
            return

        await cursor.execute(
            "INSERT INTO cart_items(cart_id, product_id, quantity) VALUES(?, ?, 1) ON CONFLICT(cart_id, product_id) DO UPDATE SET quantity = quantity + 1",
            (message.from_user.id, product_id[0]))
        await db.commit()

    await message.answer(f"{product_name} добавлен в вашу корзину!", reply_markup=choose_next_action_kb)


# Обработчик для действия "Добавить еще?"
@dp.message_handler(lambda msg: msg.text == "Добавить еще?")
async def add_more(message: types.Message):
    await view_products(message)


# Обработчик для оформления заказа
@dp.message_handler(lambda msg: msg.text == "Оформить заказ")
async def start_checkout(message: types.Message):
    await message.answer("Вы уверены, что хотите оформить заказ?",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Подтвердить заказ"),
                                                                                    KeyboardButton("Отменить заказ")))


# Обработчик для подтверждения заказа
@dp.message_handler(lambda msg: msg.text == "Подтвердить заказ")
async def confirm_checkout(message: types.Message):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("INSERT INTO orders(user_id) VALUES(?)", (message.from_user.id,))
        order_id = cursor.lastrowid
        await cursor.execute("""
        INSERT INTO order_items(order_id, product_id, quantity)
        SELECT ?, product_id, quantity FROM cart_items WHERE cart_id=?
        """, (order_id, message.from_user.id))
        await cursor.execute("DELETE FROM cart_items WHERE cart_id=?", (message.from_user.id,))
        await db.commit()

    await message.answer("Ваш заказ оформлен! В ближайшее время с вами свяжется наш менеджер.", reply_markup=main_kb)


# Обработчик команды "Отменить заказ"
@dp.message_handler(lambda msg: msg.text == "Отменить заказ")
async def cancel_checkout(message: types.Message):
    await message.answer("Заказ отменен", reply_markup=main_kb)


# Здесь мы инициализируем Redis
async def init_redis():
    global redis
    redis = Redis.from_url('redis://localhost')


# Основная точка входа
if __name__ == '__main__':
    import asyncio
    from aiogram import executor

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_redis())

    try:
        executor.start_polling(dp, skip_updates=True)
    finally:
        loop.run_until_complete(redis.close())

