import logging
from aiogram import Bot, Dispatcher, types

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Ваш токен
TOKEN = '5849978203:AAFutW7QmgnkuYglaljG2iwx-rE7IyFkOIs'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    with open("photos/foto0.jpg", "rb") as photo:
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="Доставка Шишек по острову Панган!")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
