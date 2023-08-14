import aiosqlite


async def create_database():
    """Создание таблиц, если они не существуют"""
    async with aiosqlite.connect("mydatabase.db") as db:
        # Таблица для пользователей
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            chat_id INTEGER UNIQUE
        );
        """)

        # Таблица для сортов
        await db.execute("""
        CREATE TABLE IF NOT EXISTS sorts (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            price REAL,
            photo_path TEXT
        );
        """)
        await db.commit()


if __name__ == '__main__':
    import asyncio

    asyncio.run(create_database())