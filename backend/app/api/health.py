import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


def _check_database() -> None:
    from sqlalchemy import text

    from app.db.database import engine

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _check_vector_store() -> None:
    from app.rag.vectordb import collection

    collection.count()


@router.get("/live")
def liveness():
    """Report that the API process can respond to requests."""
    return {"status": "alive"}


@router.get("/ready")
def readiness():
    """Report whether required data stores are available."""
    checks = {}

    for name, check in (
        ("database", _check_database),
        ("vector_store", _check_vector_store),
    ):
        try:
            check()
        except Exception:
            logger.exception("Readiness check failed for %s", name)
            checks[name] = "unavailable"
        else:
            checks[name] = "ok"

    if any(status != "ok" for status in checks.values()):
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}
