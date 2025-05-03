import os
from dotenv import load_dotenv
import faiss
import numpy as np
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Load environment variables
load_dotenv()
DB_DSN = os.getenv("DB_DSN")

app = FastAPI()

# In-memory storage for Faiss indices
index_store: Dict[str, faiss.IndexFlatIP] = {}


class CreateIndexRequest(BaseModel):
    key: str        # Unique identifier for the index
    dimension: int  # Dimensionality of input vectors


class SearchQuery(BaseModel):
    key: str            # Identifier of the index to query
    query: List[float]  # Query vector
    k: int = 5          # Number of nearest neighbors to return


@app.post("/create_index")
async def create_index(request: CreateIndexRequest) -> Dict[str, Any]:
    """
    Create a new Faiss index for cosine similarity search.

    Parameters:
    ----------
    request : CreateIndexRequest
        key: Unique key for the index
        dimension: Dimensionality of vectors to be stored

    Returns:
    -------
    dict
        message: Confirmation that index is created
        dimension: Dimensionality of the created index

    Raises:
    ------
    HTTPException (400)
        If an index with the given key already exists
    """
    if request.key in index_store:
        raise HTTPException(status_code=400, detail=f"Index '{request.key}' already exists.")

    index = faiss.IndexFlatIP(request.dimension)
    index_store[request.key] = index
    return {"message": f"Index '{request.key}' created.", "dimension": request.dimension}


@app.post("/add_vectors/{key}")
async def add_vectors(key: str, vectors: List[List[float]]) -> Dict[str, Any]:
    """
    Add vectors to an existing Faiss index.

    Parameters:
    ----------
    key : str
        Identifier of the index
    vectors : List[List[float]]
        Vectors to add; each vector length must match index dimensionality

    Returns:
    -------
    dict
        message: Number of vectors added and index key

    Raises:
    ------
    HTTPException (404)
        If the specified index is not found
    HTTPException (400)
        If vector dimensionality does not match index
    """
    if key not in index_store:
        raise HTTPException(status_code=404, detail=f"Index '{key}' not found.")

    index = index_store[key]
    data = np.array(vectors, dtype='float32')
    if data.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Expected dimension {index.d}, got {data.shape[1]}.")

    faiss.normalize_L2(data)
    index.add(data)
    return {"message": f"Added {len(vectors)} vectors to index '{key}'"}


@app.post("/search")
async def search(query: SearchQuery) -> Dict[str, Any]:
    """
    Search for nearest neighbors in a Faiss index using cosine similarity.

    Parameters:
    ----------
    query : SearchQuery
        key: Identifier of the index
        query: Query vector
        k: Number of neighbors to retrieve

    Returns:
    -------
    dict
        cosine_similarities: List of similarity scores
        indices: List of corresponding vector indices

    Raises:
    ------
    HTTPException (404)
        If index not found
    HTTPException (400)
        If query dimension mismatch
    """
    if query.key not in index_store:
        raise HTTPException(status_code=404, detail=f"Index '{query.key}' not found.")

    index = index_store[query.key]
    vec = np.array(query.query, dtype='float32').reshape(1, -1)
    if vec.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Expected dimension {index.d}, got {vec.shape[1]}.")

    faiss.normalize_L2(vec)
    distances, ids = index.search(vec, query.k)
    return {"cosine_similarities": distances.tolist(), "indices": ids.tolist()}


class Database:
    """
    Asynchronous PostgreSQL database access using asyncpg.
    """

    def __init__(self) -> None:
        """
        Initialize Database instance with no active pool.

        Attributes:
        ----------
        db_pool : asyncpg.Pool | None
            Connection pool (initialized in create_pool)
        """
        self.db_pool = None

    async def create_pool(self) -> None:
        """
        Establish a connection pool to the PostgreSQL database.

        Uses DSN from environment variable `DB_DSN`.

        Raises:
        ------
        asyncpg.PostgresError
            If pool creation fails.
        """
        self.db_pool = await asyncpg.create_pool(dsn=DB_DSN)

    async def register_user_if_not_exists(self, user: Any) -> None:
        """
        Insert a new user record in `communications.users` if not exists.

        Parameters:
        ----------
        user : Any
            Object with attributes: id, username, first_name, last_name

        Raises:
        ------
        asyncpg.PostgresError
            If database operation fails.
        """
        async with self.db_pool.acquire() as conn:
            uid = await conn.fetchval(
                "SELECT user_id FROM communications.users WHERE tg_chat_id = $1",
                str(user.id)
            )
            if not uid:
                await conn.execute(
                    """
                    INSERT INTO communications.users 
                    (username, tg_chat_id, forename, surname)
                    VALUES ($1, $2, $3, $4)
                    """,
                    user.username, str(user.id), user.first_name, user.last_name
                )

    async def save_feedback(self, user: Any, feedback_text: str) -> None:
        """
        Save a feedback message linked to a new thread.

        Parameters:
        ----------
        user : Any
            Object with attribute `id` representing tg_chat_id
        feedback_text : str
            Feedback content

        Raises:
        ------
        asyncpg.PostgresError
            If database operation fails.
        """
        async with self.db_pool.acquire() as conn:
            uid = await conn.fetchval(
                "SELECT user_id FROM communications.users WHERE tg_chat_id = $1",
                str(user.id)
            )
            tid = await conn.fetchval(
                "INSERT INTO communications.threads DEFAULT VALUES RETURNING thread_id"
            )
            await conn.execute(
                """
                INSERT INTO communications.messages 
                (text, thread_id, user_id, author, feedback)
                VALUES ($1, $2, $3, 'USER', 1)
                """,
                feedback_text, tid, uid
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
