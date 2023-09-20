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
main_kb.add(KeyboardButton("Посмотреть товары"), KeyboardButton("Фото сортов"))

# Клавиатура для выбора действия после добавления товара в корзину
choose_next_action_kb = ReplyKeyboardMarkup(resize_keyboard=True)
choose_next_action_kb.add(KeyboardButton("Добавить еще?"))
choose_next_action_kb.add(KeyboardButton("Оформить заказ"))
choose_next_action_kb.add(KeyboardButton("Отменить заказ"))

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Отправляем фото
    with open('photos/foto0.png', 'rb') as photo:
        await message.answer_photo(photo)
    await message.answer("Welcom Братья и Сестры!\nДоставка ТОПОВЫХ шишек!"
                         "\nПо острову Панган!\n\n ***используй кнопки внизу***", reply_markup=main_kb)

# Остальной код остается прежним...

# Теперь, после добавления товара в корзину, пользователь увидит клавиатуру choose_next_action_kb, предлагающую добавить еще товар или перейти к оформлению заказа. Если пользователь решит добавить еще товар, он нажмет кнопку "Добавить еще?", и вы снова покажете ему список товаров.

# Оформление заказа теперь доступно только после добавления товара в корзину. Если пользователь нажмет "Оформить заказ", ему будут предложены два варианта: подтвердить или отменить заказ. Если заказ подтвержден, вы можете очистить корзину этого пользователя и вернуть его к основной клавиатуре. Если заказ отменен, вы также можете вернуть пользователя к основной клавиатуре.

# Обработчик для просмотра фото сортов
@dp.message_handler(lambda msg: msg.text == "Фото сортов")
async def send_photos(message: types.Message):
    # Список всех фотографий
    photos = ["photos/foto1.jpg", "photos/foto2.jpg", "photos/foto3.jpg", "photos/foto4.jpg"]

    # Отправляем каждую фотографию в цикле
    for photo_path in photos:
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo)


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

        await message.answer("Выбери сорт:", reply_markup=kb)



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

async def get_cart_details(user_id):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT products.name, cart_items.quantity, products.price
            FROM cart_items
            JOIN products ON cart_items.product_id = products.product_id
            WHERE cart_id=?
        """, (user_id,))

        items = await cursor.fetchall()

    details = []
    for name, quantity, price in items:
        details.append(f"{name} - {quantity} грамм - {price * quantity}฿")

    return "\n".join(details)

@dp.message_handler(lambda message: message.text.isdigit())
async def handle_quantity(message: types.Message):
    quantity = int(message.text)
    user_id = message.from_user.id
    product_id_bytes = await redis.get(str(user_id))

    if not product_id_bytes:
        await message.answer("Произошла ошибка. Не удалось извлечь ID продукта.")
        return

    # Преобразуем product_id из байтовой строки в целочисленное значение
    product_id = int(product_id_bytes.decode('utf-8'))

    # Добавим вывод product_id для диагностики
    #await message.answer(f"Debug: product_id = {product_id}")

    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()

        # Получение информации о продукте
        await cursor.execute("SELECT name, price FROM products WHERE product_id=?", (product_id,))
        product_info = await cursor.fetchone()

        if not product_info:
            await message.answer("Произошла ошибка при извлечении информации о продукте.")
            return

        product_name, product_price = product_info

        # Получаем текущее количество этого товара в корзине
        await cursor.execute("SELECT quantity FROM cart_items WHERE cart_id=? AND product_id=?", (user_id, product_id))
        current_quantity_data = await cursor.fetchone()

        # Если товар уже есть в корзине, обновляем его количество
        if current_quantity_data:
            current_quantity = current_quantity_data[0]
            new_quantity = current_quantity + quantity
            await cursor.execute("UPDATE cart_items SET quantity=? WHERE cart_id=? AND product_id=?", (new_quantity, user_id, product_id))

        # Если товара еще нет в корзине, добавляем новую запись
        else:
            await cursor.execute("INSERT INTO cart_items(cart_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

        await db.commit()

    # Измененное сообщение об успешном добавлении товара в корзину
    cart_details = await get_cart_details(user_id)
    await message.answer(f"Товар в корзину:\n{cart_details}", reply_markup=choose_next_action_kb)







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

    # Получить детали заказа
    order_details = await get_order_details(order_id)

    # Формирование ссылки на пользователя
    user_mention = f"[{message.from_user.full_name}](tg://user?id={message.from_user.id})"

    # Отправляем детали заказа владельцу бота с ссылкой на пользователя
    await bot.send_message(OWNER_ID, f"Новый заказ №{order_id} от {user_mention}:\n{order_details}",
                           parse_mode="Markdown", disable_web_page_preview=False)

    # Добавляем ссылку на связь с менеджером в сообщение для пользователя
    await message.answer("Обрабатываем ваш заказ!\n"
                         "В ближайшее время с вами свяжется наш менеджер!\n"
                         "Уточним детали и возможное время доставки\n"
                         "Если менеджер не ответил, напишите [сюда](https://t.me/Babakoba)!",
                         reply_markup=main_kb, parse_mode="Markdown", disable_web_page_preview=False)


# Обработчик команды "Отменить заказ"
@dp.message_handler(lambda msg: msg.text == "Отменить заказ")
async def cancel_checkout(message: types.Message):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("DELETE FROM cart_items WHERE cart_id=?", (message.from_user.id,))
        await db.commit()

    await message.answer("Корзина очищена.", reply_markup=main_kb)


async def get_order_details(order_id):
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT products.name, order_items.quantity, products.price
            FROM order_items
            JOIN products ON order_items.product_id = products.product_id
            WHERE order_id=?
        """, (order_id,))

        items = await cursor.fetchall()

    details = []
    for name, quantity, price in items:
        details.append(f"{name} - {quantity} грамм - {price * quantity}฿")

    return "\n".join(details)


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

