import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Хранилище индексов
index_store: Dict[str, faiss.IndexFlatIP] = {}


# Модель для создания индекса
class CreateIndexRequest(BaseModel):
    key: str  # Уникальный ключ для индекса
    dimension: int  # Размерность векторов


# Модель запроса поиска
class SearchQuery(BaseModel):
    key: str  # Ключ индекса
    query: List[float]  # Вектор запроса
    k: int = 5  # Количество ближайших соседей


@app.post("/create_index")
async def create_index(request: CreateIndexRequest):
    """Создание нового индекса"""
    if request.key in index_store:
        raise HTTPException(status_code=400, detail=f"Индекс с ключом '{request.key}' уже существует.")

    # Создаем индекс для косинусного сходства
    index = faiss.IndexFlatIP(request.dimension)
    index_store[request.key] = index
    return {"message": f"Индекс '{request.key}' создан.", "dimension": request.dimension}


@app.post("/add_vectors/{key}")
async def add_vectors(key: str, vectors: List[List[float]]):
    """Добавление векторов в индекс"""
    if key not in index_store:
        raise HTTPException(status_code=404, detail=f"Индекс с ключом '{key}' не найден.")

    index = index_store[key]
    data = np.array(vectors, dtype='float32')

    if data.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Размерность векторов должна быть {index.d}.")

    faiss.normalize_L2(data)  # Нормализация векторов
    index.add(data)
    return {"message": f"{len(vectors)} векторов добавлено в индекс '{key}'."}


@app.post("/search")
async def search(query: SearchQuery):
    """Поиск ближайших соседей в указанном индексе"""
    if query.key not in index_store:
        raise HTTPException(status_code=404, detail=f"Индекс с ключом '{query.key}' не найден.")

    index = index_store[query.key]
    query_vector = np.array(query.query, dtype='float32').reshape(1, -1)

    if query_vector.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Размерность вектора запроса должна быть {index.d}.")

    faiss.normalize_L2(query_vector)  # Нормализация запроса
    distances, indices = index.search(query_vector, query.k)
    return {
        'cosine_similarities': distances.tolist(),
        'indices': indices.tolist()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
