import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_database_url(name="DATABASE_URL"):
    url = os.environ[name]
    if make_url(url).drivername != "postgresql+psycopg":
        raise ValueError("Используйте PostgreSQL: postgresql+psycopg://...")
    return url


engine = create_engine(get_database_url(), pool_pre_ping=True, hide_parameters=True)


def get_session():
    with Session(engine, expire_on_commit=False) as session:
        yield session
