import sqlite3

# Создание соединения с базой данных
connection = sqlite3.connect('shopbot.db')
cursor = connection.cursor()

# Примеры продуктов
products = [
    ("Afgan kush", 250, "http://example.com/afgan_kush"),
    ("Bruce Buner", 250, "http://example.com/bruce_buner"),
    ("Gorilla Glue", 250, "http://example.com/gorilla_glue"),
    ("Cannabis Joint set", 300, "http://example.com/cannabis_joint_set"),
]

try:
    # Вставка продуктов в таблицу, если их нет в базе данных
    for product in products:
        product_name = product[0]
        if not cursor.execute("SELECT 1 FROM products WHERE name=?", (product_name,)).fetchone():
            cursor.execute("INSERT INTO products (name, price, url) VALUES (?, ?, ?)", product)

    # Завершение транзакции
    connection.commit()
    print("Примеры продуктов были успешно добавлены в базу данных!")

except sqlite3.Error as e:
    print(f"Произошла ошибка: {e}")

finally:
    # Закрытие соединения
    connection.close()
