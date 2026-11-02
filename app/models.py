"""SQLAlchemy 2 ORM. Создание схемы выполняется только миграциями Alembic."""

from datetime import date, datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    metadata = sa.MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        comment="Дата создания (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        comment="Дата последнего изменения через ORM (UTC)",
    )


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"comment": "Роли пользователей из технического задания"}

    code: Mapped[str] = mapped_column(sa.String(32), primary_key=True, comment="Код роли")
    name: Mapped[str] = mapped_column(sa.String(100), unique=True, comment="Название роли")
    users: Mapped[list["User"]] = relationship(back_populates="role", passive_deletes="all")


class Department(TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        sa.CheckConstraint("length(trim(name)) > 0", name="name_not_blank"),
        sa.CheckConstraint("length(trim(code)) > 0", name="code_not_blank"),
        {"comment": "Подразделения предприятия"},
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(), primary_key=True, comment="Идентификатор подразделения"
    )
    code: Mapped[str] = mapped_column(sa.String(20), unique=True, comment="Уникальный код")
    name: Mapped[str] = mapped_column(sa.String(200), unique=True, comment="Название подразделения")
    is_active: Mapped[bool] = mapped_column(server_default=sa.true(), comment="Действует ли отдел")
    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department",
        passive_deletes="all",
    )
    tasks: Mapped[list["Task"]] = relationship(back_populates="department", passive_deletes="all")


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        sa.CheckConstraint("length(trim(last_name)) > 0", name="last_name_not_blank"),
        sa.CheckConstraint("length(trim(first_name)) > 0", name="first_name_not_blank"),
        sa.CheckConstraint("length(trim(position)) > 0", name="position_not_blank"),
        sa.CheckConstraint("length(trim(phone)) > 0", name="phone_not_blank"),
        sa.CheckConstraint(
            "email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'", name="email_format"
        ),
        sa.Index("uq_employees_email_lower", sa.func.lower(sa.column("email")), unique=True),
        sa.Index("ix_employees_last_name_lower", sa.func.lower(sa.column("last_name"))),
        {"comment": "Сотрудники и их текущее подразделение"},
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(), primary_key=True, comment="Идентификатор сотрудника"
    )
    department_id: Mapped[int] = mapped_column(
        sa.ForeignKey("departments.id", ondelete="RESTRICT"),
        index=True,
        comment="Текущее подразделение сотрудника",
    )
    last_name: Mapped[str] = mapped_column(sa.String(100), comment="Фамилия")
    first_name: Mapped[str] = mapped_column(sa.String(100), comment="Имя")
    middle_name: Mapped[str | None] = mapped_column(sa.String(100), comment="Отчество при наличии")
    position: Mapped[str] = mapped_column(sa.String(150), comment="Должность")
    email: Mapped[str] = mapped_column(sa.String(254), comment="Электронная почта")
    phone: Mapped[str] = mapped_column(sa.String(30), comment="Контактный телефон")
    is_active: Mapped[bool] = mapped_column(
        server_default=sa.true(), comment="Работает ли сотрудник"
    )
    department: Mapped[Department] = relationship(back_populates="employees")
    personal_data: Mapped["EmployeePersonalData | None"] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user: Mapped["User | None"] = relationship(back_populates="employee", passive_deletes="all")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
        passive_deletes="all",
    )


class EmployeePersonalData(Base):
    __tablename__ = "employee_personal_data"
    __table_args__ = (
        sa.CheckConstraint("passport_series ~ '^[0-9]{4}$'", name="passport_series_format"),
        sa.CheckConstraint("passport_number ~ '^[0-9]{6}$'", name="passport_number_format"),
        sa.CheckConstraint("inn ~ '^[0-9]{12}$'", name="inn_format"),
        sa.CheckConstraint("snils ~ '^[0-9]{11}$'", name="snils_format"),
        sa.CheckConstraint("length(trim(passport_issued_by)) > 0", name="issuer_not_blank"),
        sa.CheckConstraint("length(trim(registration_address)) > 0", name="address_not_blank"),
        sa.UniqueConstraint("passport_series", "passport_number", name="uq_employee_passport"),
        {"comment": "Кадровые персональные данные, отдельные от публичной карточки сотрудника"},
    )

    employee_id: Mapped[int] = mapped_column(
        sa.ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Идентификатор сотрудника; связь 1:0..1",
    )
    passport_series: Mapped[str] = mapped_column(sa.String(4), comment="Серия паспорта, 4 цифры")
    passport_number: Mapped[str] = mapped_column(sa.String(6), comment="Номер паспорта, 6 цифр")
    passport_issued_by: Mapped[str] = mapped_column(sa.String(500), comment="Кем выдан паспорт")
    passport_issued_on: Mapped[date] = mapped_column(comment="Дата выдачи паспорта")
    inn: Mapped[str] = mapped_column(sa.String(12), unique=True, comment="ИНН физлица, 12 цифр")
    snils: Mapped[str] = mapped_column(sa.String(11), unique=True, comment="СНИЛС без разделителей")
    registration_address: Mapped[str] = mapped_column(sa.String(500), comment="Адрес регистрации")
    employee: Mapped[Employee] = relationship(back_populates="personal_data")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.CheckConstraint("length(trim(username)) > 0", name="username_not_blank"),
        sa.CheckConstraint("length(trim(password_hash)) > 0", name="password_hash_not_blank"),
        sa.Index("uq_users_username_lower", sa.func.lower(sa.column("username")), unique=True),
        {"comment": "Учетные записи. Только хеш пароля, авторизация реализуется позднее"},
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(), primary_key=True, comment="Идентификатор учетной записи"
    )
    employee_id: Mapped[int] = mapped_column(
        sa.ForeignKey("employees.id", ondelete="RESTRICT"),
        unique=True,
        comment="Сотрудник; одна учетная запись на сотрудника",
    )
    role_code: Mapped[str] = mapped_column(
        sa.ForeignKey("roles.code", ondelete="RESTRICT"),
        server_default="employee",
        index=True,
        comment="Одна из четырех ролей ТЗ",
    )
    username: Mapped[str] = mapped_column(sa.String(100), comment="Логин без учета регистра")
    password_hash: Mapped[str] = mapped_column(sa.String(255), comment="Самоописываемый хеш пароля")
    is_active: Mapped[bool] = mapped_column(server_default=sa.true(), comment="Разрешен ли вход")
    employee: Mapped[Employee] = relationship(back_populates="user")
    role: Mapped[Role] = relationship(back_populates="users")


class TaskStatus(Base):
    __tablename__ = "task_statuses"
    __table_args__ = (
        sa.CheckConstraint("sort_order > 0", name="sort_order_positive"),
        {"comment": "Справочник колонок kanban-доски"},
    )

    code: Mapped[str] = mapped_column(sa.String(32), primary_key=True, comment="Код состояния")
    name: Mapped[str] = mapped_column(sa.String(100), unique=True, comment="Название колонки")
    sort_order: Mapped[int] = mapped_column(unique=True, comment="Порядок колонки на доске")


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        sa.CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),
        sa.CheckConstraint("priority BETWEEN 1 AND 4", name="priority_range"),
        sa.CheckConstraint("due_at IS NULL OR due_at >= created_at", name="due_after_creation"),
        sa.CheckConstraint(
            "(status_code = 'done' AND completed_at IS NOT NULL "
            "AND completed_by_id IS NOT NULL AND assignee_id IS NOT NULL) OR "
            "(status_code <> 'done' AND completed_at IS NULL AND completed_by_id IS NULL)",
            name="completion_consistent",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at", name="completion_after_creation"
        ),
        sa.Index("ix_tasks_department_status", "department_id", "status_code"),
        sa.Index("ix_tasks_assignee_due", "assignee_id", "due_at"),
        sa.Index("ix_tasks_completed_at", "completed_at"),
        {"comment": "Производственные задачи; один ответственный исполнитель"},
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(), primary_key=True, comment="Идентификатор задачи"
    )
    department_id: Mapped[int] = mapped_column(
        sa.ForeignKey("departments.id", ondelete="RESTRICT"),
        comment="Подразделение задачи",
    )
    title: Mapped[str] = mapped_column(sa.String(250), comment="Заголовок задачи")
    description: Mapped[str | None] = mapped_column(sa.Text, comment="Подробное описание")
    assignee_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("employees.id", ondelete="RESTRICT"),
        comment="Ответственный исполнитель задачи",
    )
    created_by_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        comment="Учетная запись постановщика задачи",
    )
    status_code: Mapped[str] = mapped_column(
        sa.ForeignKey("task_statuses.code", ondelete="RESTRICT"),
        server_default="new",
        comment="Текущее состояние kanban-карточки",
    )
    priority: Mapped[int] = mapped_column(
        sa.SmallInteger,
        server_default="2",
        comment="Приоритет: 1 низкий, 2 обычный, 3 высокий, 4 срочный",
    )
    due_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), comment="Плановый срок выполнения"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), comment="Фактическое время выполнения"
    )
    completed_by_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        comment="Пользователь, подтвердивший выполнение",
    )
    is_archived: Mapped[bool] = mapped_column(
        server_default=sa.false(), comment="Скрыта ли карточка с рабочей доски"
    )
    department: Mapped[Department] = relationship(back_populates="tasks")
    assignee: Mapped[Employee | None] = relationship(
        back_populates="tasks",
        foreign_keys=[assignee_id],
        primaryjoin="Task.assignee_id == Employee.id",
    )
    creator: Mapped[User] = relationship(foreign_keys=[created_by_id])
    completer: Mapped[User | None] = relationship(foreign_keys=[completed_by_id])
    status: Mapped[TaskStatus] = relationship()
    history: Mapped[list["TaskStatusHistory"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(TaskStatusHistory.changed_at, TaskStatusHistory.id)",
    )

    @hybrid_property
    def is_overdue(self) -> bool:
        return (
            self.due_at is not None
            and self.due_at < datetime.now(timezone.utc)
            and self.status_code not in {"done", "cancelled"}
        )

    @is_overdue.inplace.expression
    @classmethod
    def _is_overdue_expression(cls):
        return sa.and_(
            cls.due_at.is_not(None),
            cls.due_at < sa.func.now(),
            cls.status_code.not_in(("done", "cancelled")),
        )


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"
    __table_args__ = (
        sa.CheckConstraint(
            "from_status_code IS NULL OR from_status_code <> to_status_code", name="status_changed"
        ),
        sa.Index("ix_task_status_history_task_changed", "task_id", "changed_at"),
        {"comment": "События смены состояния. Заполняются сервисом в транзакции изменения задачи"},
    )

    id: Mapped[int] = mapped_column(
        sa.BigInteger, sa.Identity(), primary_key=True, comment="Идентификатор события"
    )
    task_id: Mapped[int] = mapped_column(
        sa.ForeignKey("tasks.id", ondelete="CASCADE"),
        comment="Задача, состояние которой изменилось",
    )
    from_status_code: Mapped[str | None] = mapped_column(
        sa.ForeignKey("task_statuses.code", ondelete="RESTRICT"),
        comment="Предыдущее состояние; NULL при создании",
    )
    to_status_code: Mapped[str] = mapped_column(
        sa.ForeignKey("task_statuses.code", ondelete="RESTRICT"),
        comment="Новое состояние",
    )
    changed_by_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        comment="Пользователь, выполнивший действие",
    )
    changed_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), comment="Время события"
    )
    comment: Mapped[str | None] = mapped_column(sa.Text, comment="Комментарий к изменению")
    task: Mapped[Task] = relationship(back_populates="history")
    from_status: Mapped[TaskStatus | None] = relationship(foreign_keys=[from_status_code])
    to_status: Mapped[TaskStatus] = relationship(foreign_keys=[to_status_code])
    changed_by: Mapped[User] = relationship()
