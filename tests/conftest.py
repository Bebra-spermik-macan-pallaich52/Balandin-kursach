"""Каждый тест работает в отдельной временной схеме PostgreSQL."""

import os
import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database():
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.fail("Задайте TEST_DATABASE_URL: тесты требуют настоящую PostgreSQL")
    url = make_url(raw_url)
    if url.get_backend_name() != "postgresql":
        pytest.fail("Тестовая СУБД должна быть PostgreSQL")
    schema = "test_" + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    # public намеренно исключен: его alembic_version не должен влиять на тестовую схему.
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine, config
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def session(database):
    with Session(database[0], expire_on_commit=False) as session:
        yield session


@pytest.fixture
def sample(session):
    from app.models import Department, Employee, Task, User

    department = Department(code="TEST", name="Тестовый цех")
    other_department = Department(code="OTHER", name="Другой цех")
    session.add_all([department, other_department])
    session.flush()
    employee = Employee(
        department_id=department.id,
        last_name="Баландин",
        first_name="Артём",
        middle_name="Александрович",
        email="balandin@example.test",
        phone="+70000000000",
        position="Инженер",
    )
    session.add(employee)
    session.flush()
    user = User(
        employee_id=employee.id,
        username="balandin",
        password_hash="test-hash",
        role_code="department_head",
    )
    session.add(user)
    session.flush()
    task = Task(
        department_id=department.id,
        title="Проверить оборудование",
        assignee_id=employee.id,
        created_by_id=user.id,
    )
    session.add(task)
    session.commit()
    return department, other_department, employee, user, task
