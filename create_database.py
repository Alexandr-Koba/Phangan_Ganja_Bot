import aiosqlite

DATABASE = "marihuana.db"

async def create_database():
    async with aiosqlite.connect(DATABASE) as conn:
        cursor = await conn.cursor()

        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS sorts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price INTEGER,
            photo_path TEXT
        )
        ''')

        await cursor.execute("INSERT INTO sorts (name, description, price, photo_path) VALUES (?, ?, ?, ?)",
              ("Afgan Kush", "Описание Afgan Kush", 250, "photos/foto1.jpg"))

        await cursor.execute("INSERT INTO sorts (name, description, price, photo_path) VALUES (?, ?, ?, ?)",
              ("Gorilla Glue", "Описание Gorilla Glue", 300, "photos/foto2.jpg"))

        await cursor.execute("INSERT INTO sorts (name, description, price, photo_path) VALUES (?, ?, ?, ?)",
              ("Bruce Buner", "Описание Bruce Buner", 350, "photos/foto3.jpg"))

        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS making_order (
            user_contact INTEGER,
            sort_order TEXT,
            gramm INTEGER
        )
        ''')

        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer INTEGER,
            sort_order TEXT,
            gramm_order INTEGER
        )
        ''')

        await cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            chat_id INTEGER UNIQUE
        )
        ''')

        await conn.commit()

async def main():
    await create_database()
    print("База данных и таблицы успешно созданы!")

import asyncio
asyncio.run(main())
