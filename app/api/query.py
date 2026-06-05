from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

from fastapi import APIRouter

from app.models.query import QueryRequest
from app.models.retrieval import RetrievalResponse
from app.services.retriever import retrieve_relevant_chunks

router = APIRouter()


@router.post("/query", response_model=RetrievalResponse)
def query_documents(request: QueryRequest):

    results = retrieve_relevant_chunks(
        request.question,
        request.top_k
    )

    return {
        "question": request.question,
        "results": results
    }