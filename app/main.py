from fastapi import FastAPI

from app.api.upload import router as upload_router


app = FastAPI(
    title="Exam Intelligence API",
    version="1.0.0"
)


app.include_router(
    upload_router,
    prefix="/api"
)


@app.get("/")
def home():

    return {
        "message": "Exam Intelligence Server Running"
    }

from fastapi import FastAPI

from app.api.upload import router as upload_router
from app.api.query import router as query_router

app = FastAPI()

app.include_router(upload_router)
app.include_router(query_router)

from app.api.chat import router as chat_router
app.include_router(chat_router)