import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DB_DSN = os.getenv("DB_DSN")

class Database:
    def __init__(self):
        self.db_pool = None

    async def create_pool(self):
        self.db_pool = await asyncpg.create_pool(dsn=DB_DSN)

    async def register_user_if_not_exists(self, user):
        async with self.db_pool.acquire() as conn:
            user_id = await conn.fetchval(
                "select user_id from communications.users where tg_chat_id = $1",
                str(user.id)
            )
            if not user_id:
                await conn.execute(
                    """
                    insert into communications.users (username, tg_chat_id, forename, surname)
                    values ($1, $2, $3, $4)
                    """,
                    user.username, str(user.id), user.first_name, user.last_name
                )

    async def save_feedback(self, user, feedback_text):
        async with self.db_pool.acquire() as conn:
            user_id = await conn.fetchval(
                "select user_id from communications.users where tg_chat_id = $1",
                str(user.id)
            )
            thread_id = await conn.fetchval(
                "insert into communications.threads default values returning thread_id"
            )
            await conn.execute(
                """
                insert into communications.messages (text, thread_id, user_id, author, feedback)
                values ($1, $2, $3, 'USER', 1)
                """,
                feedback_text, thread_id, user_id
            )
