from typing import Annotated, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_session

app = FastAPI(
    title="АРМ учета производственных задач",
    version="0.1.0",
    description="Этап 1: ORM SQLAlchemy и миграции PostgreSQL. Доступны служебные проверки.",
)


class Health(BaseModel):
    status: Literal["ok"] = "ok"


class DatabaseHealth(Health):
    database: Literal["ok"] = "ok"
    api_version: Literal["v1", "v2"]


@app.get("/health/live", response_model=Health, tags=["Состояние"])
def liveness() -> Health:
    """Процесс запущен. Соединение с БД не требуется."""
    return Health()


def make_health_router(version: Literal["v1", "v2"]) -> APIRouter:
    router = APIRouter(prefix=f"/api/{version}", tags=[f"Состояние {version}"])

    @router.get("/health", response_model=DatabaseHealth)
    def database_health(session: Annotated[Session, Depends(get_session)]) -> DatabaseHealth:
        try:
            session.execute(text("SELECT 1"))
            # Проверяется не только доступность сервера, но и наличие обеих миграций.
            revision = session.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0002":
                raise HTTPException(
                    status_code=503, detail="Примените миграции: alembic upgrade head"
                )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503, detail="База данных недоступна или не подготовлена"
            )
        return DatabaseHealth(api_version=version)

    return router


app.include_router(make_health_router("v1"))
app.include_router(make_health_router("v2"))
