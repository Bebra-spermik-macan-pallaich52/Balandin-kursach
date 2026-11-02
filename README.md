# Учёт производственных задач

Этап курсовой: ORM-модели SQLAlchemy и миграции PostgreSQL для FastAPI.
Нужны Python 3.11+ и установленная PostgreSQL 17.

## Настройки

Приложение, миграции и тесты читают настройки из файла `.env` в корне проекта:

```dotenv
DATABASE_URL=postgresql+psycopg://coursework:coursework_local@localhost:5432/coursework
TEST_DATABASE_URL=postgresql+psycopg://coursework:coursework_local@localhost:5432/coursework_test
```

В первой строке находится основная БД, во второй — отдельная БД для тестов.
Укажите в них свой логин, пароль, порт и названия баз. Переменные окружения терминала
имеют приоритет над `.env`. Если пароль содержит `@`, `:`, `/`, `#` или `%`,
эти символы в URL нужно записать в percent-encoding, например `@` как `%40`.
После изменения `.env` перезапустите приложение.

Если базы ещё не созданы, откройте **SQL Shell (psql)** из меню «Пуск»,
подключитесь пользователем `postgres` и выполните команды по одной:

```sql
CREATE ROLE coursework LOGIN PASSWORD 'coursework_local';
CREATE DATABASE coursework OWNER coursework;
CREATE DATABASE coursework_test OWNER coursework;
```

Они соответствуют локальным учебным параметрам в `.env`.
Уже существующие роль и базы повторно создавать не нужно.

## Запуск в PowerShell

Откройте терминал в папке проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Если `.venv` уже существует, первую команду пропустите.
Чтобы убрать пакеты от предыдущей версии проекта, удалите старую папку `.venv`
и создайте окружение заново этими командами.
На Linux/macOS вместо `.venv\Scripts\` используется `.venv/bin/`.

Swagger: http://127.0.0.1:8000/docs

Проверка PostgreSQL и миграций: http://127.0.0.1:8000/api/v1/health
или `/api/v2/health`. Успешный ответ: `{"status":"ok","database":"ok"}`.
Проверка процесса без обращения к БД: `/health/live`.

## Данные и проверки

Загрузить учебный набор данных:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
```

Скрипт создаёт 50 подразделений, 100 сотрудников и их личных карточек,
100 отключённых учётных записей, 200 задач и 350 событий истории.
Повторный запуск не добавляет дубли. Роли и состояния добавляются миграцией.

Запустить тесты на БД из `TEST_DATABASE_URL`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Тесты используют отдельные временные схемы PostgreSQL и удаляют их после проверки.

## Файлы

- `app/models.py` — сотрудники, подразделения, личные данные, пользователи, роли и задачи.
- `app/database.py` — чтение `.env`, подключение и сессия БД.
- `app/main.py` — FastAPI и служебные маршруты.
- `alembic/` — две миграции и шаблон для последующих изменений.
- `scripts/seed_demo.py` — учебные данные.
- `tests/` — проверка моделей, миграций, настроек и маршрутов.
- `docs/erd.svg` — ER-диаграмма, `docs/data_dictionary.md` — словарь полей БД.

Текущая ревизия: `0002`. Проверить соответствие моделей схеме:

```powershell
.\.venv\Scripts\alembic.exe check
```

CRUD, авторизация и отчёты относятся к следующим этапам курсовой.
