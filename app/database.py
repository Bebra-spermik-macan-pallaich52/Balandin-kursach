from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)


def get_session() -> Generator[Session, None, None]:
    """Сессия на запрос; будущие сервисы явно управляют commit/rollback."""
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session
