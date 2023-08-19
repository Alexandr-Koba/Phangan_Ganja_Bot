import aiosqlite

# Создание таблицы продуктов
CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL
);
"""

# Создание корзины для каждого пользователя
CREATE_CART_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS cart_items (
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    UNIQUE (cart_id, product_id)
);
"""

# Создание таблицы заказов
CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL
);
"""

# Создание таблицы элементов заказа
CREATE_ORDER_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

async def main():
    async with aiosqlite.connect("shopbot.db") as db:
        cursor = await db.cursor()
        await cursor.execute(CREATE_PRODUCTS_TABLE)
        await cursor.execute(CREATE_CART_ITEMS_TABLE)
        await cursor.execute(CREATE_ORDERS_TABLE)
        await cursor.execute(CREATE_ORDER_ITEMS_TABLE)
        await db.commit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
