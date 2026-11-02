import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
            comment="Идентификатор подразделения",
        ),
        sa.Column("code", sa.String(length=20), nullable=False, comment="Уникальный код"),
        sa.Column("name", sa.String(length=200), nullable=False, comment="Название подразделения"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="Действует ли отдел",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего изменения через ORM (UTC)",
        ),
        sa.CheckConstraint("length(trim(code)) > 0", name=op.f("ck_departments_code_not_blank")),
        sa.CheckConstraint("length(trim(name)) > 0", name=op.f("ck_departments_name_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_departments")),
        sa.UniqueConstraint("code", name=op.f("uq_departments_code")),
        sa.UniqueConstraint("name", name=op.f("uq_departments_name")),
        comment="Подразделения предприятия",
    )
    op.create_table(
        "roles",
        sa.Column("code", sa.String(length=32), nullable=False, comment="Код роли"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Название роли"),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
        comment="Роли пользователей из технического задания",
    )
    op.create_table(
        "task_statuses",
        sa.Column("code", sa.String(length=32), nullable=False, comment="Код состояния"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Название колонки"),
        sa.Column("sort_order", sa.Integer(), nullable=False, comment="Порядок колонки на доске"),
        sa.CheckConstraint("sort_order > 0", name=op.f("ck_task_statuses_sort_order_positive")),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_task_statuses")),
        sa.UniqueConstraint("name", name=op.f("uq_task_statuses_name")),
        sa.UniqueConstraint("sort_order", name=op.f("uq_task_statuses_sort_order")),
        comment="Справочник колонок kanban-доски",
    )
    op.create_table(
        "employees",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
            comment="Идентификатор сотрудника",
        ),
        sa.Column(
            "department_id",
            sa.BigInteger(),
            nullable=False,
            comment="Текущее подразделение сотрудника",
        ),
        sa.Column("last_name", sa.String(length=100), nullable=False, comment="Фамилия"),
        sa.Column("first_name", sa.String(length=100), nullable=False, comment="Имя"),
        sa.Column(
            "middle_name", sa.String(length=100), nullable=True, comment="Отчество при наличии"
        ),
        sa.Column("position", sa.String(length=150), nullable=False, comment="Должность"),
        sa.Column("email", sa.String(length=254), nullable=False, comment="Электронная почта"),
        sa.Column("phone", sa.String(length=30), nullable=False, comment="Контактный телефон"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="Работает ли сотрудник",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего изменения через ORM (UTC)",
        ),
        sa.CheckConstraint(
            "email ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'",
            name=op.f("ck_employees_email_format"),
        ),
        sa.CheckConstraint(
            "length(trim(first_name)) > 0", name=op.f("ck_employees_first_name_not_blank")
        ),
        sa.CheckConstraint(
            "length(trim(last_name)) > 0", name=op.f("ck_employees_last_name_not_blank")
        ),
        sa.CheckConstraint("length(trim(phone)) > 0", name=op.f("ck_employees_phone_not_blank")),
        sa.CheckConstraint(
            "length(trim(position)) > 0", name=op.f("ck_employees_position_not_blank")
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_employees_department_id_departments"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
        comment="Сотрудники и их текущее подразделение",
    )
    op.create_index(
        op.f("ix_employees_department_id"), "employees", ["department_id"], unique=False
    )
    op.create_index(
        "ix_employees_last_name_lower",
        "employees",
        [sa.literal_column("lower(last_name)")],
        unique=False,
    )
    op.create_index(
        "uq_employees_email_lower", "employees", [sa.literal_column("lower(email)")], unique=True
    )
    op.create_table(
        "employee_personal_data",
        sa.Column(
            "employee_id",
            sa.BigInteger(),
            nullable=False,
            comment="Идентификатор сотрудника; связь 1:0..1",
        ),
        sa.Column(
            "passport_series",
            sa.String(length=4),
            nullable=False,
            comment="Серия паспорта, 4 цифры",
        ),
        sa.Column(
            "passport_number", sa.String(length=6), nullable=False, comment="Номер паспорта, 6 цифр"
        ),
        sa.Column(
            "passport_issued_by", sa.String(length=500), nullable=False, comment="Кем выдан паспорт"
        ),
        sa.Column("passport_issued_on", sa.Date(), nullable=False, comment="Дата выдачи паспорта"),
        sa.Column("inn", sa.String(length=12), nullable=False, comment="ИНН физлица, 12 цифр"),
        sa.Column("snils", sa.String(length=11), nullable=False, comment="СНИЛС без разделителей"),
        sa.Column(
            "registration_address",
            sa.String(length=500),
            nullable=False,
            comment="Адрес регистрации",
        ),
        sa.CheckConstraint(
            "inn ~ '^[0-9]{12}$'", name=op.f("ck_employee_personal_data_inn_format")
        ),
        sa.CheckConstraint(
            "passport_number ~ '^[0-9]{6}$'",
            name=op.f("ck_employee_personal_data_passport_number_format"),
        ),
        sa.CheckConstraint(
            "passport_series ~ '^[0-9]{4}$'",
            name=op.f("ck_employee_personal_data_passport_series_format"),
        ),
        sa.CheckConstraint(
            "snils ~ '^[0-9]{11}$'", name=op.f("ck_employee_personal_data_snils_format")
        ),
        sa.CheckConstraint(
            "length(trim(passport_issued_by)) > 0",
            name=op.f("ck_employee_personal_data_issuer_not_blank"),
        ),
        sa.CheckConstraint(
            "length(trim(registration_address)) > 0",
            name=op.f("ck_employee_personal_data_address_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_employee_personal_data_employee_id_employees"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("employee_id", name=op.f("pk_employee_personal_data")),
        sa.UniqueConstraint("inn", name=op.f("uq_employee_personal_data_inn")),
        sa.UniqueConstraint("passport_series", "passport_number", name="uq_employee_passport"),
        sa.UniqueConstraint("snils", name=op.f("uq_employee_personal_data_snils")),
        comment="Кадровые персональные данные, отдельные от публичной карточки сотрудника",
    )
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
            comment="Идентификатор учетной записи",
        ),
        sa.Column(
            "employee_id",
            sa.BigInteger(),
            nullable=False,
            comment="Сотрудник; одна учетная запись на сотрудника",
        ),
        sa.Column(
            "role_code",
            sa.String(length=32),
            server_default="employee",
            nullable=False,
            comment="Одна из четырех ролей ТЗ",
        ),
        sa.Column(
            "username", sa.String(length=100), nullable=False, comment="Логин без учета регистра"
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="Самоописываемый хеш пароля",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="Разрешен ли вход",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего изменения через ORM (UTC)",
        ),
        sa.CheckConstraint(
            "length(trim(password_hash)) > 0", name=op.f("ck_users_password_hash_not_blank")
        ),
        sa.CheckConstraint("length(trim(username)) > 0", name=op.f("ck_users_username_not_blank")),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name=op.f("fk_users_employee_id_employees"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_code"],
            ["roles.code"],
            name=op.f("fk_users_role_code_roles"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("employee_id", name=op.f("uq_users_employee_id")),
        comment="Учетные записи. Только хеш пароля, авторизация реализуется позднее",
    )
    op.create_index(op.f("ix_users_role_code"), "users", ["role_code"], unique=False)
    op.create_index(
        "uq_users_username_lower", "users", [sa.literal_column("lower(username)")], unique=True
    )
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
            comment="Идентификатор задачи",
        ),
        sa.Column("department_id", sa.BigInteger(), nullable=False, comment="Подразделение задачи"),
        sa.Column("title", sa.String(length=250), nullable=False, comment="Заголовок задачи"),
        sa.Column("description", sa.Text(), nullable=True, comment="Подробное описание"),
        sa.Column(
            "assignee_id",
            sa.BigInteger(),
            nullable=True,
            comment="Ответственный исполнитель задачи",
        ),
        sa.Column(
            "created_by_id",
            sa.BigInteger(),
            nullable=False,
            comment="Учетная запись постановщика задачи",
        ),
        sa.Column(
            "status_code",
            sa.String(length=32),
            server_default="new",
            nullable=False,
            comment="Текущее состояние kanban-карточки",
        ),
        sa.Column(
            "priority",
            sa.SmallInteger(),
            server_default="2",
            nullable=False,
            comment="Приоритет: 1 низкий, 2 обычный, 3 высокий, 4 срочный",
        ),
        sa.Column(
            "due_at", sa.DateTime(timezone=True), nullable=True, comment="Плановый срок выполнения"
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Фактическое время выполнения",
        ),
        sa.Column(
            "completed_by_id",
            sa.BigInteger(),
            nullable=True,
            comment="Пользователь, подтвердивший выполнение",
        ),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="Скрыта ли карточка с рабочей доски",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата последнего изменения через ORM (UTC)",
        ),
        sa.CheckConstraint(
            "(status_code = 'done' AND completed_at IS NOT NULL AND completed_by_id IS NOT NULL AND assignee_id IS NOT NULL) OR (status_code <> 'done' AND completed_at IS NULL AND completed_by_id IS NULL)",
            name=op.f("ck_tasks_completion_consistent"),
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name=op.f("ck_tasks_completion_after_creation"),
        ),
        sa.CheckConstraint(
            "due_at IS NULL OR due_at >= created_at", name=op.f("ck_tasks_due_after_creation")
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name=op.f("ck_tasks_title_not_blank")),
        sa.CheckConstraint("priority BETWEEN 1 AND 4", name=op.f("ck_tasks_priority_range")),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["employees.id"],
            name=op.f("fk_tasks_assignee_id_employees"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["completed_by_id"],
            ["users.id"],
            name=op.f("fk_tasks_completed_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_tasks_created_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name=op.f("fk_tasks_department_id_departments"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["status_code"],
            ["task_statuses.code"],
            name=op.f("fk_tasks_status_code_task_statuses"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
        comment="Производственные задачи; один ответственный исполнитель",
    )
    op.create_index("ix_tasks_assignee_due", "tasks", ["assignee_id", "due_at"], unique=False)
    op.create_index("ix_tasks_completed_at", "tasks", ["completed_at"], unique=False)
    op.create_index(op.f("ix_tasks_completed_by_id"), "tasks", ["completed_by_id"], unique=False)
    op.create_index(op.f("ix_tasks_created_by_id"), "tasks", ["created_by_id"], unique=False)
    op.create_index(
        "ix_tasks_department_status", "tasks", ["department_id", "status_code"], unique=False
    )
    op.create_table(
        "task_status_history",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
            comment="Идентификатор события",
        ),
        sa.Column(
            "task_id",
            sa.BigInteger(),
            nullable=False,
            comment="Задача, состояние которой изменилось",
        ),
        sa.Column(
            "from_status_code",
            sa.String(length=32),
            nullable=True,
            comment="Предыдущее состояние; NULL при создании",
        ),
        sa.Column(
            "to_status_code", sa.String(length=32), nullable=False, comment="Новое состояние"
        ),
        sa.Column(
            "changed_by_id",
            sa.BigInteger(),
            nullable=False,
            comment="Пользователь, выполнивший действие",
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Время события",
        ),
        sa.Column("comment", sa.Text(), nullable=True, comment="Комментарий к изменению"),
        sa.CheckConstraint(
            "from_status_code IS NULL OR from_status_code <> to_status_code",
            name=op.f("ck_task_status_history_status_changed"),
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_id"],
            ["users.id"],
            name=op.f("fk_task_status_history_changed_by_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["from_status_code"],
            ["task_statuses.code"],
            name=op.f("fk_task_status_history_from_status_code_task_statuses"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_task_status_history_task_id_tasks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_status_code"],
            ["task_statuses.code"],
            name=op.f("fk_task_status_history_to_status_code_task_statuses"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_status_history")),
        comment="События смены состояния. Заполняются сервисом в транзакции изменения задачи",
    )
    op.create_index(
        op.f("ix_task_status_history_changed_by_id"),
        "task_status_history",
        ["changed_by_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_status_history_task_changed",
        "task_status_history",
        ["task_id", "changed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_status_history_task_changed", table_name="task_status_history")
    op.drop_index(op.f("ix_task_status_history_changed_by_id"), table_name="task_status_history")
    op.drop_table("task_status_history")
    op.drop_index("ix_tasks_department_status", table_name="tasks")
    op.drop_index(op.f("ix_tasks_created_by_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_completed_by_id"), table_name="tasks")
    op.drop_index("ix_tasks_completed_at", table_name="tasks")
    op.drop_index("ix_tasks_assignee_due", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("uq_users_username_lower", table_name="users")
    op.drop_index(op.f("ix_users_role_code"), table_name="users")
    op.drop_table("users")
    op.drop_table("employee_personal_data")
    op.drop_index("uq_employees_email_lower", table_name="employees")
    op.drop_index("ix_employees_last_name_lower", table_name="employees")
    op.drop_index(op.f("ix_employees_department_id"), table_name="employees")
    op.drop_table("employees")
    op.drop_table("task_statuses")
    op.drop_table("roles")
    op.drop_table("departments")
