import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from alembic import command
from app.database import get_database_url

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database():
    url = make_url(get_database_url("TEST_DATABASE_URL"))
    schema = "test_" + uuid.uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield (engine, config)
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
    return (department, other_department, employee, user, task)
