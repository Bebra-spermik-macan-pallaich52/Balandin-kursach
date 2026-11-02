# Словарь данных PostgreSQL

Сформирован из примененной схемы, включая PK, FK, UNIQUE, CHECK и индексы.
UQ — уникальность одного поля; UQ* — участие в составном UNIQUE (паспорт).
Таблица alembic_version является служебной и в предметную модель не входит.
Временные метки — TIMESTAMP WITH TIME ZONE; отображение задается часовым поясом клиента.

## departments

Подразделения предприятия

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `id` | BIGINT | Нет | IDENTITY | Идентификатор подразделения |
| UQ | `code` | VARCHAR(20) | Нет | — | Уникальный код |
| UQ | `name` | VARCHAR(200) | Нет | — | Название подразделения |
| — | `is_active` | BOOLEAN | Нет | true | Действует ли отдел |
| — | `created_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата создания (UTC) |
| — | `updated_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата последнего изменения через ORM (UTC) |

Внешние ключи:

Нет.

Ограничения и индексы:

- UNIQUE `uq_departments_code`: code.
- UNIQUE `uq_departments_name`: name.
- CHECK `ck_departments_code_not_blank`: `length(TRIM(BOTH FROM code)) > 0`.
- CHECK `ck_departments_name_not_blank`: `length(TRIM(BOTH FROM name)) > 0`.
- INDEX `uq_departments_code`: ['code']; unique=True.
- INDEX `uq_departments_name`: ['name']; unique=True.

## employees

Сотрудники и их текущее подразделение

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `id` | BIGINT | Нет | IDENTITY | Идентификатор сотрудника |
| FK | `department_id` | BIGINT | Нет | — | Текущее подразделение сотрудника |
| — | `last_name` | VARCHAR(100) | Нет | — | Фамилия |
| — | `first_name` | VARCHAR(100) | Нет | — | Имя |
| — | `middle_name` | VARCHAR(100) | Да | — | Отчество при наличии |
| — | `position` | VARCHAR(150) | Нет | — | Должность |
| — | `email` | VARCHAR(254) | Нет | — | Электронная почта |
| — | `phone` | VARCHAR(30) | Нет | — | Контактный телефон |
| — | `is_active` | BOOLEAN | Нет | true | Работает ли сотрудник |
| — | `created_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата создания (UTC) |
| — | `updated_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата последнего изменения через ORM (UTC) |

Внешние ключи:

- `department_id` → `departments.id`, ON DELETE RESTRICT.

Ограничения и индексы:

- CHECK `ck_employees_email_format`: `email::text ~ '^[^[:space:]@]+@[^[:space:]@]+[.][^[:space:]@]+$'::text`.
- CHECK `ck_employees_first_name_not_blank`: `length(TRIM(BOTH FROM first_name)) > 0`.
- CHECK `ck_employees_last_name_not_blank`: `length(TRIM(BOTH FROM last_name)) > 0`.
- CHECK `ck_employees_phone_not_blank`: `length(TRIM(BOTH FROM phone)) > 0`.
- CHECK `ck_employees_position_not_blank`: `length(TRIM(BOTH FROM "position")) > 0`.
- INDEX `ix_employees_department_id`: ['department_id']; unique=False.
- INDEX `ix_employees_last_name_lower`: ['lower(last_name::text)']; unique=False.
- INDEX `uq_employees_email_lower`: ['lower(email::text)']; unique=True.

## employee_personal_data

Кадровые персональные данные, отдельные от публичной карточки сотрудника

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK, FK | `employee_id` | BIGINT | Нет | — | Идентификатор сотрудника; связь 1:0..1 |
| UQ* | `passport_series` | VARCHAR(4) | Нет | — | Серия паспорта, 4 цифры |
| UQ* | `passport_number` | VARCHAR(6) | Нет | — | Номер паспорта, 6 цифр |
| — | `passport_issued_by` | VARCHAR(500) | Нет | — | Кем выдан паспорт |
| — | `passport_issued_on` | DATE | Нет | — | Дата выдачи паспорта |
| UQ | `inn` | VARCHAR(12) | Нет | — | ИНН физлица, 12 цифр |
| UQ | `snils` | VARCHAR(11) | Нет | — | СНИЛС без разделителей |
| — | `registration_address` | VARCHAR(500) | Нет | — | Адрес регистрации |

Внешние ключи:

- `employee_id` → `employees.id`, ON DELETE CASCADE.

Ограничения и индексы:

- UNIQUE `uq_employee_passport`: passport_series, passport_number.
- UNIQUE `uq_employee_personal_data_inn`: inn.
- UNIQUE `uq_employee_personal_data_snils`: snils.
- CHECK `ck_employee_personal_data_address_not_blank`: `length(TRIM(BOTH FROM registration_address)) > 0`.
- CHECK `ck_employee_personal_data_inn_format`: `inn::text ~ '^[0-9]{12}$'::text`.
- CHECK `ck_employee_personal_data_issuer_not_blank`: `length(TRIM(BOTH FROM passport_issued_by)) > 0`.
- CHECK `ck_employee_personal_data_passport_number_format`: `passport_number::text ~ '^[0-9]{6}$'::text`.
- CHECK `ck_employee_personal_data_passport_series_format`: `passport_series::text ~ '^[0-9]{4}$'::text`.
- CHECK `ck_employee_personal_data_snils_format`: `snils::text ~ '^[0-9]{11}$'::text`.
- INDEX `uq_employee_passport`: ['passport_series', 'passport_number']; unique=True.
- INDEX `uq_employee_personal_data_inn`: ['inn']; unique=True.
- INDEX `uq_employee_personal_data_snils`: ['snils']; unique=True.

## users

Учетные записи. Только хеш пароля, авторизация реализуется позднее

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `id` | BIGINT | Нет | IDENTITY | Идентификатор учетной записи |
| FK, UQ | `employee_id` | BIGINT | Нет | — | Сотрудник; одна учетная запись на сотрудника |
| FK | `role_code` | VARCHAR(32) | Нет | 'employee'::character varying | Одна из четырех ролей ТЗ |
| — | `username` | VARCHAR(100) | Нет | — | Логин без учета регистра |
| — | `password_hash` | VARCHAR(255) | Нет | — | Самоописываемый хеш пароля |
| — | `is_active` | BOOLEAN | Нет | true | Разрешен ли вход |
| — | `created_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата создания (UTC) |
| — | `updated_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата последнего изменения через ORM (UTC) |

Внешние ключи:

- `employee_id` → `employees.id`, ON DELETE RESTRICT.
- `role_code` → `roles.code`, ON DELETE RESTRICT.

Ограничения и индексы:

- UNIQUE `uq_users_employee_id`: employee_id.
- CHECK `ck_users_password_hash_not_blank`: `length(TRIM(BOTH FROM password_hash)) > 0`.
- CHECK `ck_users_username_not_blank`: `length(TRIM(BOTH FROM username)) > 0`.
- INDEX `ix_users_role_code`: ['role_code']; unique=False.
- INDEX `uq_users_employee_id`: ['employee_id']; unique=True.
- INDEX `uq_users_username_lower`: ['lower(username::text)']; unique=True.

## roles

Роли пользователей из технического задания

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `code` | VARCHAR(32) | Нет | — | Код роли |
| UQ | `name` | VARCHAR(100) | Нет | — | Название роли |

Внешние ключи:

Нет.

Ограничения и индексы:

- UNIQUE `uq_roles_name`: name.
- INDEX `uq_roles_name`: ['name']; unique=True.

## tasks

Производственные задачи; один ответственный исполнитель

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `id` | BIGINT | Нет | IDENTITY | Идентификатор задачи |
| FK | `department_id` | BIGINT | Нет | — | Подразделение задачи |
| — | `title` | VARCHAR(250) | Нет | — | Заголовок задачи |
| — | `description` | TEXT | Да | — | Подробное описание |
| FK | `assignee_id` | BIGINT | Да | — | Ответственный исполнитель задачи |
| FK | `created_by_id` | BIGINT | Нет | — | Учетная запись постановщика задачи |
| FK | `status_code` | VARCHAR(32) | Нет | 'new'::character varying | Текущее состояние kanban-карточки |
| — | `priority` | SMALLINT | Нет | '2'::smallint | Приоритет: 1 низкий, 2 обычный, 3 высокий, 4 срочный |
| — | `due_at` | TIMESTAMP WITH TIME ZONE | Да | — | Плановый срок выполнения |
| — | `completed_at` | TIMESTAMP WITH TIME ZONE | Да | — | Фактическое время выполнения |
| FK | `completed_by_id` | BIGINT | Да | — | Пользователь, подтвердивший выполнение |
| — | `is_archived` | BOOLEAN | Нет | false | Скрыта ли карточка с рабочей доски |
| — | `created_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата создания (UTC) |
| — | `updated_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Дата последнего изменения через ORM (UTC) |

Внешние ключи:

- `assignee_id` → `employees.id`, ON DELETE RESTRICT.
- `completed_by_id` → `users.id`, ON DELETE RESTRICT.
- `created_by_id` → `users.id`, ON DELETE RESTRICT.
- `department_id` → `departments.id`, ON DELETE RESTRICT.
- `status_code` → `task_statuses.code`, ON DELETE RESTRICT.

Ограничения и индексы:

- CHECK `ck_tasks_completion_after_creation`: `completed_at IS NULL OR completed_at >= created_at`.
- CHECK `ck_tasks_completion_consistent`: `status_code::text = 'done'::text AND completed_at IS NOT NULL AND completed_by_id IS NOT NULL AND assignee_id IS NOT NULL OR status_code::text <> 'done'::text AND completed_at IS NULL AND completed_by_id IS NULL`.
- CHECK `ck_tasks_due_after_creation`: `due_at IS NULL OR due_at >= created_at`.
- CHECK `ck_tasks_priority_range`: `priority >= 1 AND priority <= 4`.
- CHECK `ck_tasks_title_not_blank`: `length(TRIM(BOTH FROM title)) > 0`.
- INDEX `ix_tasks_assignee_due`: ['assignee_id', 'due_at']; unique=False.
- INDEX `ix_tasks_completed_at`: ['completed_at']; unique=False.
- INDEX `ix_tasks_completed_by_id`: ['completed_by_id']; unique=False.
- INDEX `ix_tasks_created_by_id`: ['created_by_id']; unique=False.
- INDEX `ix_tasks_department_status`: ['department_id', 'status_code']; unique=False.

## task_statuses

Справочник колонок kanban-доски

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `code` | VARCHAR(32) | Нет | — | Код состояния |
| UQ | `name` | VARCHAR(100) | Нет | — | Название колонки |
| UQ | `sort_order` | INTEGER | Нет | — | Порядок колонки на доске |

Внешние ключи:

Нет.

Ограничения и индексы:

- UNIQUE `uq_task_statuses_name`: name.
- UNIQUE `uq_task_statuses_sort_order`: sort_order.
- CHECK `ck_task_statuses_sort_order_positive`: `sort_order > 0`.
- INDEX `uq_task_statuses_name`: ['name']; unique=True.
- INDEX `uq_task_statuses_sort_order`: ['sort_order']; unique=True.

## task_status_history

События смены состояния. Заполняются сервисом в транзакции изменения задачи

| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |
|---|---|---|---|---|---|
| PK | `id` | BIGINT | Нет | IDENTITY | Идентификатор события |
| FK | `task_id` | BIGINT | Нет | — | Задача, состояние которой изменилось |
| FK | `from_status_code` | VARCHAR(32) | Да | — | Предыдущее состояние; NULL при создании |
| FK | `to_status_code` | VARCHAR(32) | Нет | — | Новое состояние |
| FK | `changed_by_id` | BIGINT | Нет | — | Пользователь, выполнивший действие |
| — | `changed_at` | TIMESTAMP WITH TIME ZONE | Нет | now() | Время события |
| — | `comment` | TEXT | Да | — | Комментарий к изменению |

Внешние ключи:

- `changed_by_id` → `users.id`, ON DELETE RESTRICT.
- `from_status_code` → `task_statuses.code`, ON DELETE RESTRICT.
- `task_id` → `tasks.id`, ON DELETE CASCADE.
- `to_status_code` → `task_statuses.code`, ON DELETE RESTRICT.

Ограничения и индексы:

- CHECK `ck_task_status_history_status_changed`: `from_status_code IS NULL OR from_status_code::text <> to_status_code::text`.
- INDEX `ix_task_status_history_changed_by_id`: ['changed_by_id']; unique=False.
- INDEX `ix_task_status_history_task_changed`: ['task_id', 'changed_at']; unique=False.
