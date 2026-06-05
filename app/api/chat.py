from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse

from app.services.retriever import retrieve_relevant_chunks
from app.services.prompt_builder import build_prompt
from app.services.llm import generate_answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # STEP 1: Retrieve chunks
    retrieved_chunks = retrieve_relevant_chunks(
        request.question,
        request.top_k
    )

    # STEP 2: Build prompt
    prompt = build_prompt(
        request.question,
        retrieved_chunks
    )

    # STEP 3: Generate answer
    answer = generate_answer(prompt)

    # STEP 4: Return response
    return {
        "question": request.question,
        "answer": answer,
        "sources": retrieved_chunks
    }