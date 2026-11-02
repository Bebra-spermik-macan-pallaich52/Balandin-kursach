from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import DataError, IntegrityError

from alembic import command
from app.models import (
    Base,
    Employee,
    EmployeePersonalData,
    Role,
    Task,
    TaskStatus,
    TaskStatusHistory,
    User,
)


def test_upgrade_and_model_match(database):
    engine, config = database
    tables = set(inspect(engine).get_table_names())
    assert tables == set(Base.metadata.tables) | {"alembic_version"}
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.check(config)


def test_downgrade_and_reupgrade(database):
    engine, config = database
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM roles")) == 4
        assert connection.scalar(text("SELECT count(*) FROM task_statuses")) == 4


def test_reference_data(session):
    assert set(session.scalars(select(Role.code))) == {
        "admin",
        "director",
        "department_head",
        "employee",
    }
    assert set(session.scalars(select(TaskStatus.code))) == {
        "new",
        "in_progress",
        "done",
        "cancelled",
    }


def test_relationships_and_defaults(session, sample):
    department, _, employee, user, task = sample
    assert employee.department is department
    assert user.employee is employee
    assert user.role.code == "department_head"
    assert task.assignee is employee
    assert task.creator is user
    assert task.department is department
    assert task.status_code == "new"
    assert task.created_at.tzinfo is not None
    assert task.priority == 2


@pytest.mark.parametrize(
    "field,value",
    [
        ("last_name", ""),
        ("first_name", "   "),
        ("email", "invalid-email"),
    ],
)
def test_employee_validation(session, sample, field, value):
    setattr(sample[2], field, value)
    with pytest.raises(IntegrityError):
        session.commit()


def test_unique_email_case_insensitive(session, sample):
    employee = sample[2]
    session.add(
        Employee(
            department_id=employee.department_id,
            last_name="Другой",
            first_name="Сотрудник",
            email=employee.email.upper(),
            phone="+70000000001",
            position="Техник",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_user_one_to_one(session, sample):
    session.add(User(employee_id=sample[2].id, username="second", password_hash="test-hash"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_role(session, sample):
    sample[3].role_code = "unknown"
    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    "field,value",
    [
        ("passport_series", "12xx"),
        ("passport_number", "123"),
        ("inn", "12345678901x"),
        ("snils", "123-456-789 00"),
    ],
)
def test_personal_data_format(session, sample, field, value):
    fields = dict(
        employee_id=sample[2].id,
        passport_series="0000",
        passport_number="000001",
        passport_issued_by="Тестовый орган",
        passport_issued_on=datetime(2020, 1, 1).date(),
        inn="000000000001",
        snils="00000000001",
        registration_address="Тестовый адрес",
    )
    fields[field] = value
    session.add(EmployeePersonalData(**fields))
    with pytest.raises((IntegrityError, DataError)):
        session.commit()


def test_personal_data_unique(session, sample):
    def details(employee_id, snils):
        return EmployeePersonalData(
            employee_id=employee_id,
            passport_series="0000",
            passport_number="000001",
            passport_issued_by="Тестовый орган",
            passport_issued_on=datetime(2020, 1, 1).date(),
            inn=f"{employee_id:012}",
            snils=snils,
            registration_address="Тестовый адрес",
        )

    other = Employee(
        department_id=sample[0].id,
        last_name="Иванов",
        first_name="Иван",
        email="ivanov@example.test",
        phone="+70000000002",
        position="Мастер",
    )
    session.add(other)
    session.flush()
    session.add_all([details(sample[2].id, "00000000001"), details(other.id, "00000000002")])
    with pytest.raises(IntegrityError):
        session.commit()


def test_assignee_must_exist(session, sample):
    sample[4].assignee_id = 999999999
    with pytest.raises(IntegrityError):
        session.commit()


def test_employee_transfer_preserves_task_department(session, sample):
    sample[2].department_id = sample[1].id
    session.commit()
    assert sample[4].department_id == sample[0].id
    assert sample[4].assignee_id == sample[2].id


def test_task_can_be_unassigned(session, sample):
    sample[4].assignee_id = None
    session.commit()
    assert sample[4].assignee is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("priority", 0),
        ("priority", 5),
        ("title", " "),
        ("status_code", "unknown"),
        ("due_at", datetime(2000, 1, 1, tzinfo=timezone.utc)),
        ("completed_at", datetime.now(timezone.utc)),
        ("status_code", "done"),
    ],
)
def test_task_invalid_state(session, sample, field, value):
    setattr(sample[4], field, value)
    with pytest.raises(IntegrityError):
        session.commit()


def test_complete_task_and_history(session, sample):
    task, user = sample[4], sample[3]
    task.status_code = "done"
    task.completed_at = datetime.now(timezone.utc)
    task.completed_by_id = user.id
    session.add(
        TaskStatusHistory(
            task_id=task.id,
            from_status_code="new",
            to_status_code="done",
            changed_by_id=user.id,
            comment="Выполнение подтверждено руководителем",
        )
    )
    session.commit()
    assert task.completer is user
    assert len(task.history) == 1
    assert task.history[0].to_status.code == "done"


def test_overdue_is_computed(session, sample):
    task = sample[4]
    task.created_at = datetime.now(timezone.utc) - timedelta(days=2)
    task.due_at = datetime.now(timezone.utc) - timedelta(days=1)
    session.commit()
    assert task.is_overdue
    assert session.scalar(select(Task.id).where(Task.is_overdue)) == task.id


def test_restrict_delete_employee_with_task(session, sample):
    with pytest.raises(IntegrityError):
        session.execute(text("DELETE FROM employees WHERE id=:id"), {"id": sample[2].id})
        session.commit()


def test_restrict_delete_department(session, sample):
    with pytest.raises(IntegrityError):
        session.execute(text("DELETE FROM departments WHERE id=:id"), {"id": sample[0].id})
        session.commit()


def test_personal_data_deleted_with_unused_employee(session, sample):
    other = Employee(
        department_id=sample[0].id,
        last_name="Сидоров",
        first_name="Пётр",
        email="sidorov@example.test",
        phone="+70000000003",
        position="Стажёр",
    )
    session.add(other)
    session.flush()
    session.add(
        EmployeePersonalData(
            employee_id=other.id,
            passport_series="0000",
            passport_number="000003",
            passport_issued_by="Тестовый орган",
            passport_issued_on=datetime(2020, 1, 1).date(),
            inn="000000000003",
            snils="00000000003",
            registration_address="Тестовый адрес",
        )
    )
    session.commit()
    session.delete(other)
    session.commit()
    assert session.scalar(select(func.count()).select_from(EmployeePersonalData)) == 0


def test_demo_seed_is_repeatable(database):
    from scripts.seed_demo import seed

    engine, _ = database
    seed(engine)
    seed(engine)
    with engine.connect() as connection:
        for table, count in {
            "departments": 50,
            "employees": 100,
            "employee_personal_data": 100,
            "users": 100,
            "tasks": 200,
            "task_status_history": 350,
        }.items():
            assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == count
        assert connection.scalar(text("SELECT count(*) FROM tasks WHERE status_code='done'")) > 0
