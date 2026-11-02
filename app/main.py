from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_session

app = FastAPI(title="АРМ учета производственных задач")


@app.get("/health/live")
def liveness():
    return {"status": "ok"}


@app.get("/api/v1/health")
@app.get("/api/v2/health")
def database_health(session: Session = Depends(get_session)):
    try:
        revision = session.scalar(text("SELECT version_num FROM alembic_version"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="База данных недоступна или не подготовлена")
    if revision != "0002":
        raise HTTPException(status_code=503, detail="Примените миграции: alembic upgrade head")
    return {"status": "ok", "database": "ok"}
