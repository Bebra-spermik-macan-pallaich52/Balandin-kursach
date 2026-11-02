import base64
import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.database import engine
from app.models import (
    Department,
    Employee,
    EmployeePersonalData,
    Task,
    TaskStatusHistory,
    User,
)

SURNAMES = [
    "Иванов",
    "Петров",
    "Сидоров",
    "Смирнов",
    "Кузнецов",
    "Попов",
    "Васильев",
    "Соколов",
    "Михайлов",
    "Новиков",
    "Фёдоров",
    "Морозов",
    "Волков",
    "Алексеев",
    "Лебедев",
    "Семёнов",
    "Егоров",
    "Павлов",
    "Козлов",
    "Степанов",
]
NAMES = ["Александр", "Артём", "Иван", "Пётр", "Сергей", "Дмитрий", "Николай", "Михаил"]
WORK = [
    "Проверить оборудование линии",
    "Подготовить производственный отчёт",
    "Выполнить плановое обслуживание",
    "Проверить качество партии",
    "Обновить технологическую карту",
    "Провести инвентаризацию инструмента",
    "Настроить производственный стенд",
    "Согласовать график работ",
]


def disabled_password_hash() -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secrets.token_bytes(32), salt, 600000)
    return (
        "pbkdf2_sha256$600000$"
        + base64.b64encode(salt).decode()
        + "$"
        + base64.b64encode(digest).decode()
    )


def seed(engine: Engine) -> bool:
    with Session(engine) as session, session.begin():
        existing = session.scalars(
            select(Department.code).where(Department.code.like("DEMO%"))
        ).all()
        if existing:
            expected = {f"DEMO{i:02d}" for i in range(1, 51)}
            if set(existing) != expected:
                raise RuntimeError("Обнаружен неполный набор DEMO-подразделений")
            return False
        departments = [
            Department(code=f"DEMO{i:02d}", name=f"Учебный производственный участок № {i:02d}")
            for i in range(1, 51)
        ]
        session.add_all(departments)
        session.flush()
        employees = []
        users = []
        for i in range(1, 101):
            employee = Employee(
                department_id=departments[(i - 1) // 2].id,
                last_name=SURNAMES[(i - 1) % len(SURNAMES)],
                first_name=NAMES[(i - 1) % len(NAMES)],
                middle_name="Александрович",
                position="Мастер участка" if i % 2 else "Техник",
                email=f"employee{i:03d}@example.test",
                phone=f"+700000{i:05d}",
            )
            session.add(employee)
            session.flush()
            session.add(
                EmployeePersonalData(
                    employee_id=employee.id,
                    passport_series="0000",
                    passport_number=f"{i:06d}",
                    passport_issued_by="Вымышленный орган, учебные данные",
                    passport_issued_on=date(2020, 1, 15),
                    inn=f"{i:012d}",
                    snils=f"{i:011d}",
                    registration_address=f"Учебный город, улица Тестовая, дом {i}",
                )
            )
            role = "department_head" if i % 2 else "employee"
            if i == 1:
                role = "admin"
            elif i == 2:
                role = "director"
            user = User(
                employee_id=employee.id,
                username=f"demo{i:03d}",
                role_code=role,
                password_hash=disabled_password_hash(),
                is_active=False,
            )
            session.add(user)
            employees.append(employee)
            users.append(user)
        session.flush()
        now = datetime.now(timezone.utc)
        for i in range(200):
            employee = employees[i % 100]
            creator = users[i % 100 // 2 * 2]
            status = ("new", "in_progress", "done", "cancelled")[i % 4]
            created_at = now - timedelta(days=15 + i % 120)
            due_at = created_at + timedelta(days=10 + i % 40)
            completed_at = created_at + timedelta(days=5) if status == "done" else None
            changed_at = completed_at or created_at + timedelta(days=1)
            task = Task(
                department_id=employee.department_id,
                assignee_id=employee.id,
                created_by_id=creator.id,
                title=f"{WORK[i % len(WORK)]} № {i + 1}",
                description="Демонстрационная производственная задача для проверки модели.",
                status_code=status,
                priority=i % 4 + 1,
                created_at=created_at,
                updated_at=changed_at if status != "new" else created_at,
                due_at=due_at,
                completed_at=completed_at,
                completed_by_id=creator.id if status == "done" else None,
            )
            session.add(task)
            session.flush()
            session.add(
                TaskStatusHistory(
                    task_id=task.id,
                    from_status_code=None,
                    to_status_code="new",
                    changed_by_id=creator.id,
                    changed_at=created_at,
                    comment="Создание задачи",
                )
            )
            if status != "new":
                session.add(
                    TaskStatusHistory(
                        task_id=task.id,
                        from_status_code="new",
                        to_status_code=status,
                        changed_by_id=creator.id,
                        changed_at=changed_at,
                        comment="Учебное изменение состояния",
                    )
                )
    return True


def main() -> None:
    inserted = seed(engine)
    print("Демо-данные добавлены." if inserted else "Демо-данные уже присутствуют.")


if __name__ == "__main__":
    main()
