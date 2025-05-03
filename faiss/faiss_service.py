import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

# Storage for Faiss indices
index_store: Dict[str, faiss.IndexFlatIP] = {}


class CreateIndexRequest(BaseModel):
    key: str        # Unique identifier for the index
    dimension: int  # Vector dimensionality


class SearchQuery(BaseModel):
    key: str         # Identifier of the index to search
    query: List[float]  # Query vector
    k: int = 5         # Number of nearest neighbors to return (default: 5)


@app.post("/create_index")
async def create_index(request: CreateIndexRequest):
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
        raise HTTPException(status_code=400, detail=f"Index with key '{request.key}' already exists.")

    index = faiss.IndexFlatIP(request.dimension)
    index_store[request.key] = index
    return {"message": f"Index '{request.key}' created.", "dimension": request.dimension}


@app.post("/add_vectors/{key}")
async def add_vectors(key: str, vectors: List[List[float]]):
    """
    Add vectors to an existing Faiss index.

    Parameters:
    ----------
    key : str
        Identifier of the index
    vectors : List[List[float]]
        List of vectors to add (each vector must match index dimensionality)

    Returns:
    -------
    dict
        message: Number of vectors added and index key

    Raises:
    ------
    HTTPException (404)
        If the specified index is not found
    HTTPException (400)
        If vector dimensionality does not match the index
    """
    if key not in index_store:
        raise HTTPException(status_code=404, detail=f"Index with key '{key}' not found.")

    index = index_store[key]
    data = np.array(vectors, dtype='float32')

    if data.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Vector dimensionality must be {index.d}.")

    faiss.normalize_L2(data)
    index.add(data)
    return {"message": f"{len(vectors)} vectors added to index '{key}'."}


@app.post("/search")
async def search(query: SearchQuery):
    """
    Search for nearest neighbors in a Faiss index using cosine similarity.

    Parameters:
    ----------
    query : SearchQuery
        key: Identifier of the index to search
        query: Query vector
        k: Number of nearest neighbors to retrieve

    Returns:
    -------
    dict
        cosine_similarities: List of similarity scores
        indices: List of indices of nearest vectors

    Raises:
    ------
    HTTPException (404)
        If the specified index is not found
    HTTPException (400)
        If query vector dimensionality does not match the index
    """
    if query.key not in index_store:
        raise HTTPException(status_code=404, detail=f"Index with key '{query.key}' not found.")

    index = index_store[query.key]
    query_vector = np.array(query.query, dtype='float32').reshape(1, -1)

    if query_vector.shape[1] != index.d:
        raise HTTPException(status_code=400, detail=f"Query vector dimensionality must be {index.d}.")

    faiss.normalize_L2(query_vector)
    distances, indices = index.search(query_vector, query.k)
    return {
        'cosine_similarities': distances.tolist(),
        'indices': indices.tolist()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
