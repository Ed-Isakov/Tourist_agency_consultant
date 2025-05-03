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
import httpx

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AGENT_URL = os.getenv("AGENT_URL")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = Database()


class FeedbackState(StatesGroup):
    """
    States group for feedback FSM.
    """
    waiting_feedback = State()


# Main keyboard with a single button for feedback
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Оставить отзыв")]],
    resize_keyboard=True
)


async def on_startup(dp: Dispatcher) -> None:
    """
    Actions to run on bot startup.

    Connects to the database pool.

    Parameters:
    ----------
    dp : Dispatcher
        Aiogram Dispatcher instance (unused)

    Returns:
    -------
    None
    """
    await db.create_pool()
    print("Бот запущен и подключился к БД.")


@dp.message_handler(Command("start"))
async def start(message: types.Message) -> None:
    """
    Handle '/start' command.

    Sends a welcome message and registers the user in the database if new.

    Parameters:
    ----------
    message : types.Message
        Incoming Telegram message object

    Returns:
    -------
    None

    Raises:
    ------
    Exception
        If database operation fails
    """
    welcome_text = (
        "🎉 Привет! Я — ваш бот-консультант по туризму. 🌍✈️\n\n"
        "Вот что я могу для вас:\n"
        "✅ Помогу с бронированием туров и авиабилетов.\n"
        "✅ Подскажу, как добраться от А до Б.\n"
        "✅ Расскажу о достопримечательностях и отелях.\n"
        "✅ Помогу с визами и другими туристическими вопросами.\n\n"
        "Если нужно, просто напишите! 😊"
    )
    await message.answer(welcome_text, reply_markup=main_kb)
    await db.register_user_if_not_exists(message.from_user)


@dp.message_handler(Text(equals="оставить отзыв", ignore_case=True))
async def feedback_request(message: types.Message, state: FSMContext) -> None:
    """
    Prompt user to provide feedback.

    Sets the FSM state to waiting for feedback.

    Parameters:
    ----------
    message : types.Message
        Incoming Telegram message triggering feedback
    state : FSMContext
        FSM context manager

    Returns:
    -------
    None
    """
    await message.answer("Пожалуйста, напишите ваш отзыв:")
    await FeedbackState.waiting_feedback.set()


@dp.message_handler(state=FeedbackState.waiting_feedback)
async def save_feedback(message: types.Message, state: FSMContext) -> None:
    """
    Save user feedback to the database.

    Parameters:
    ----------
    message : types.Message
        Incoming message containing feedback text
    state : FSMContext
        FSM context manager

    Returns:
    -------
    None

    Raises:
    ------
    Exception
        If database operation fails
    """
    await db.save_feedback(message.from_user, message.text)
    await message.answer("Спасибо за отзыв!", reply_markup=main_kb)
    await state.finish()


@dp.message_handler()
async def handle_message(message: types.Message) -> None:
    """
    Forward general messages to the external agent service and respond.

    Sends user message to AGENT_URL, returns agent's response or error message.

    Parameters:
    ----------
    message : types.Message
        Incoming Telegram message

    Returns:
    -------
    None

    Notes:
    -----
    Uses httpx.AsyncClient for HTTP requests.
    """
    payload = {"message": message.text, "thread_id": str(message.from_user.id)}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(AGENT_URL, json=payload, timeout=200.0)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "Агент вернул пустой ответ.")
        except httpx.RequestError:
            text = "Не удалось связаться с сервисом агента."
        except httpx.HTTPStatusError as e:
            text = f"Ошибка от агента: {e.response.status_code}"
        except ValueError:
            text = "Некорректный формат ответа от агента."
    await message.answer(text, reply_markup=main_kb)


if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
