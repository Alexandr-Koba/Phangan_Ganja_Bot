import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Основная клавиатура для пользователя
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("Посмотреть товары"), KeyboardButton("Просмотреть корзину"))
main_kb.add(KeyboardButton("Оформить заказ"))

# Клавиатура для выбора действия после добавления товара в корзину
choose_next_action_kb = ReplyKeyboardMarkup(resize_keyboard=True)
choose_next_action_kb.add(KeyboardButton("Добавить еще?"))
choose_next_action_kb.add(KeyboardButton("Оформить заказ"))

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в магазин! Что вы хотите сделать?", reply_markup=main_kb)

@dp.message_handler(lambda msg: msg.text == "Посмотреть товары")
async def view_products(message: types.Message):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("SELECT name, price FROM products")
        products = await cursor.fetchall()

        if not products:
            await message.answer("Извините, товары отсутствуют!")
            return

        # Создаем клавиатуру с кнопками для каждого товара
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for name, _ in products:
            btn = KeyboardButton(f"Добавить {name} в корзину")
            keyboard.add(btn)

        await message.answer("Выберите товар для добавления в корзину:", reply_markup=keyboard)


@dp.message_handler(lambda msg: "Добавить" in msg.text and "в корзину" in msg.text)
async def add_to_cart(message: types.Message):
    # Измененная логика извлечения имени продукта
    product_name = " ".join(message.text.split()[1:-2])

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


@dp.message_handler(lambda msg: msg.text == "Добавить еще?")
async def add_more(message: types.Message):
    await view_products(message)

@dp.message_handler(lambda msg: msg.text == "Оформить заказ")
async def start_checkout(message: types.Message):
    await message.answer("Вы уверены, что хотите оформить заказ?",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Подтвердить заказ"),
                                                                                    KeyboardButton("Отменить заказ")))

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

    await message.answer("Ваш заказ оформлен!", reply_markup=main_kb)

    await cursor.execute("""
    SELECT name, price, order_items.quantity
    FROM order_items
    JOIN products ON order_items.product_id = products.product_id
    WHERE order_id=?
    """, (order_id,))
    items = await cursor.fetchall()

    order_details = "\n".join([f"{name} - {price}₽ (x{quantity})" for name, price, quantity in items])
    await bot.send_message(OWNER_ID,
                           f"Новый заказ от {message.from_user.full_name} ({message.from_user.id}):\n\n{order_details}")


@dp.message_handler(lambda msg: msg.text == "Просмотреть корзину")
async def view_cart(message: types.Message):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()

        await cursor.execute("""
        SELECT name, price, cart_items.quantity
        FROM cart_items
        JOIN products ON cart_items.product_id = products.product_id
        WHERE cart_id=?
        """, (message.from_user.id,))

        items = await cursor.fetchall()

        if not items:
            await message.answer("Ваша корзина пуста!")
            return

        cart_details = "\n".join([f"{name} - {price}₽ (x{quantity})" for name, price, quantity in items])
        total_price = sum([price * quantity for _, price, quantity in items])

        await message.answer(f"Ваша корзина:\n\n{cart_details}\n\nОбщая сумма: {total_price}₽", reply_markup=main_kb)


@dp.message_handler(lambda msg: msg.text == "Отменить заказ")
async def cancel_checkout(message: types.Message):
    await message.answer("Заказ отменен", reply_markup=main_kb)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
