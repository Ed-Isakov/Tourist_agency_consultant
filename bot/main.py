import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from database import Database

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = Database()


class FeedbackState(StatesGroup):
    waiting_feedback = State()


main_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Оставить отзыв")]], resize_keyboard=True)


async def on_startup(_):
    await db.create_pool()
    print("Бот запущен и подключился к БД.")


@dp.message_handler(Command("start"))
async def start(message: types.Message):
    await message.answer("""
🎉 Привет! Я — ваш бот-консультант по туризму. 🌍✈️

Вот, что я могу для вас:
✅ Помогу с бронированием туров и авиабилетами.
✅ Подскажу, как добраться от А до Б.
✅ Расскажу о достопримечательностях и отелях.
✅ Помогу с визами и другими туристическими вопросами.

Если нужно, просто напишите! 😊
""", reply_markup=main_kb)
    await db.register_user_if_not_exists(message.from_user)


@dp.message_handler(Text(equals="оставить отзыв", ignore_case=True))
async def feedback_request(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, напишите ваш отзыв:")
    await FeedbackState.waiting_feedback.set()


@dp.message_handler(state=FeedbackState.waiting_feedback)
async def save_feedback(message: types.Message, state: FSMContext):
    await db.save_feedback(message.from_user, message.text)
    await message.answer("Спасибо за отзыв!", reply_markup=main_kb)
    await state.finish()


@dp.message_handler()
async def handle_message(message: types.Message):
    await message.answer("Ответ модели", reply_markup=main_kb)


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
