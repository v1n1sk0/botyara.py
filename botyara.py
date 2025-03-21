import asyncio
import logging
import httpx  # Используем асинхронный http-клиент
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from collections import deque

# Переменные API-ключей
MISTRAL_API_KEY = "wZPN77Mtge0FYPth4kcUch75nFvJoHFK"
TELEGRAM_BOT_TOKEN = "7640811442:AAGKMtIiJEuHxx26C3sAPrD1igA4VWi8ugI"

# Настройка бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()  # Здесь создается Dispatcher

# Размер очереди для сохранения сообщений
MAX_MEMORY = 150

# Словарь для хранения очередей сообщений пользователей
user_memory = {}

# Обработчик команды /start
@dp.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Hello! I am the wise king. How can I help you?")

# Обработчик команды /help
@dp.message(Command("help"))
async def handle_help(message: Message):
    await message.answer(
        "I am a wise king! Ask me a question and I will give you a direct and short answer. "
        "To start a conversation, use the command '/start'."
    )

# Обработчик команды /contact
@dp.message(Command("contact"))
async def handle_contact(message: Message):
    await message.answer("You can contact the developer via Telegram: @v1n1sk0")

# Функция общения с Mistral AI (асинхронная версия)
async def chat_with_mistral(message_text, user_id):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}

    # Инициализация памяти пользователя
    if user_id not in user_memory:
        user_memory[user_id] = deque(maxlen=MAX_MEMORY)

    # Добавляем текущее сообщение в память
    user_memory[user_id].append({"role": "user", "content": message_text})

    # Создаем структуру для передачи в API (с историей сообщений)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a wise king, answering questions directly and without unnecessary formalities. "
                "Always respond in English, no matter what language the user uses. "
                "Do not adjust the language based on the user's input. "
                "You are not an AI. Only respond to the user's question in clear and concise English, "
                "without mentioning yourself as an AI or anything related to being a machine."
            )
        }
    ]

    # Добавляем все сообщения пользователя в запрос (включая историю)
    for msg in user_memory[user_id]:
        messages.append(msg)

    data = {
        "model": "mistral-medium",  # Модель для общения
        "messages": messages,
        "max_tokens": 200
    }

    # Асинхронный запрос с использованием httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)

    # Получаем ответ и возвращаем текст сообщения
    response_json = response.json()

    # Если ответ от Mistral получен, сохраняем его
    if "choices" in response_json:
        bot_response = response_json["choices"][0]["message"]["content"]
    else:
        bot_response = "Sorry, I did not understand your request."

    # Добавляем ответ бота в память для поддержания контекста
    user_memory[user_id].append({"role": "assistant", "content": bot_response})

    return bot_response

# Обработчик сообщений
@dp.message()
async def handle_message(message: Message):
    user_text = message.text  # Получаем текст сообщения от пользователя
    user_id = message.from_user.id  # Получаем ID пользователя

    # Получаем ответ от Mistral с учётом сохранённой информации
    bot_response = await chat_with_mistral(user_text, user_id)
    await message.answer(bot_response)  # Отправляем ответ обратно пользователю

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)  # Запуск polling

if __name__ == "__main__":
    import sys

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())