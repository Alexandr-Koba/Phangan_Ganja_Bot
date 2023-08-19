import sqlite3

# Создание соединения с базой данных
connection = sqlite3.connect('shopbot.db')
cursor = connection.cursor()

# Примеры продуктов
products = [
    ("Afgan kush", 250),
    ("Bruce Buner", 300),
    ("Gorilla Glue", 250)
]

# Вставка продуктов в таблицу
for product in products:
    cursor.execute("INSERT INTO products (name, price) VALUES (?, ?)", product)

# Завершение транзакции и закрытие соединения
connection.commit()
connection.close()

print("Примеры продуктов были успешно добавлены в базу данных!")
