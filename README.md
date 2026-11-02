# Курсовая работа Баландина А. А. — этап 1

**Тема:** «Создание и тестирование АРМ по учету производственных задач, выполняемых
сотрудниками предприятия».

Выполнен этап **«Создание ORM-модели и миграция БД»** для будущего REST-сервиса FastAPI.
Источник предметных требований — «Баландин.pdf». В проекте используются **PostgreSQL 17,
SQLAlchemy 2 и Alembic**. SQLite не используется: методичка прямо запрещает встроенную СУБД.

В архиве находятся исходники, две миграции, демонстрационные данные, тесты, физическая
ER-диаграмма, словарь полей и краткая пояснительная записка по этому этапу.
Полный CRUD, JWT, права доступа, поиск, экспорт Word/Excel, диаграммы и Django относятся
к последующим этапам. Сейчас HTTP-интерфейс содержит только проверки работоспособности;
v1 и v2 подготовлены как отдельные префиксы, функциональных различий между ними пока нет.

## 1. Быстрый запуск

Нужны Python **3.11+**, Docker Engine / Docker Desktop с Compose v2.
Проверка выполнена на Python 3.12.14 и PostgreSQL 17; версии библиотек сохранены в
`requirements.lock`. Выполняйте команды **из корня распакованного проекта**.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d --wait db
alembic upgrade head
alembic current
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

### Windows PowerShell

Активация окружения не требуется:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
docker compose up -d --wait db
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\python.exe -m scripts.seed_demo
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Ожидаемая текущая ревизия: `0002 (head)`.

- Swagger UI: <http://127.0.0.1:8000/docs>.
- Процесс: <http://127.0.0.1:8000/health/live>.
- PostgreSQL и миграции: <http://127.0.0.1:8000/api/v1/health> и `/api/v2/health`.
- Успешный ответ проверки БД: `{"status":"ok","database":"ok","api_version":"v1"}`.
- При недоступной БД / отсутствии миграций: HTTP 503 без раскрытия параметров подключения.

Сервер **не вызывает `Base.metadata.create_all()`**. Таблицы создаются только Alembic.
Для обычного запуска без тестовых инструментов достаточно `requirements.txt`.
`.env.example` содержит локальные учебные параметры; при изменении пароля замените его
в `POSTGRES_PASSWORD` и `DATABASE_URL`. Спецсимволы пароля в URL нужно percent-encode.
Данные PostgreSQL сохраняются в Docker volume при `docker compose down`.

### Если PostgreSQL уже установлена

Создайте пользователя и пустую БД, назначьте пользователю права на схему `public`.
В `.env` укажите свой `DATABASE_URL` с префиксом `postgresql+psycopg://`.
Docker в таком случае не нужен. Далее выполняются те же команды Alembic и Uvicorn.
Сервер PostgreSQL должен существовать заранее: Alembic создает таблицы, а не саму БД.
Для иной версии PostgreSQL совместимость отдельно не проверялась.

## 2. Что создано

| ORM-класс | Таблица | Назначение |
|---|---|---|
| Role | roles | 4 роли из ТЗ |
| Department | departments | Подразделения предприятия |
| Employee | employees | ФИО, контакты, должность и подразделение |
| EmployeePersonalData | employee_personal_data | Паспорт, ИНН, СНИЛС, адрес |
| User | users | Учетная запись сотрудника и роль |
| TaskStatus | task_statuses | Колонки kanban-доски |
| Task | tasks | Сроки, исполнитель, постановщик и подтверждение выполнения |
| TaskStatusHistory | task_status_history | События смены состояния задачи |

В `alembic_version` хранится техническая ревизия, это не девятая предметная сущность.
Подробное объяснение ограничений и принятых решений — в [docs/design.md](docs/design.md).

## 3. Миграции

1. `0001_initial_schema.py`: восемь таблиц, PK/FK, UNIQUE, CHECK, индексы и комментарии.
2. `0002_reference_data.py`: четыре роли и четыре состояния (`new`, `in_progress`, `done`,
   `cancelled`). Это обязательные справочники, а не демонстрационные данные.

```bash
alembic upgrade head
alembic current
alembic check
```

`alembic check` должен вывести `No new upgrade operations detected`.
Он проверяет различия, поддерживаемые автогенерацией Alembic; CHECK дополнительно
проверяются интеграционными тестами.

На **пустой учебной БД** можно проверить обратимость:

```bash
alembic downgrade base
alembic upgrade head
```

Откат удаляет таблицы и данные. При уже загруженных задачах и пользователях откат
`0002` остановится на внешних ключах RESTRICT: справочники нельзя удалить, пока они
используются. В автотесте откат выполняется на пустой временной схеме.

SQL обеих миграций для просмотра находится в `docs/migrations.sql`. Сгенерировать заново:

```bash
alembic upgrade head --sql > docs/migrations.sql
```

Для дальнейших изменений моделей создавайте **новую** миграцию:

```bash
alembic revision --autogenerate -m "describe_change"
alembic upgrade head
```

## 4. Демонстрационные данные

```bash
python -m scripts.seed_demo
```

Создаются 50 учебных производственных участков, 100 сотрудников, 100 комплектов кадровых
данных, 100 отключенных учетных записей, 200 задач и 350 событий истории.
Роли и состояния содержат по четыре записи: их набор ограничен предметной областью.
Так выполняется требование методички о 50+ записях в несправочных сущностях.
Данные моделируют крупное предприятие с двумя работниками на каждом учебном участке;
название реального предприятия в задании не указано.

Все ФИО и реквизиты синтетические; почта использует `example.test`, номера документов
учебные, ИНН/СНИЛС не проверяются на контрольные суммы. У каждого демо-пользователя хеш
случайного неизвестного пароля и `is_active=false`. Готовых аккаунтов для входа нет:
аутентификация в этот этап не входит. Хеширование 100 паролей может занять несколько секунд.

Вся загрузка транзакционная. Повторный запуск пропускает уже загруженный набор по кодам
`DEMO01`–`DEMO50`, частичный набор подразделений вызывает ошибку. Скрипт не восстанавливает
вручную удаленные записи уже загруженного полного набора.

## 5. Проверка

Сначала создайте **отдельную тестовую БД** (один раз):

```bash
docker compose exec db createdb -U coursework coursework_test
```

Если пользователь изменен в `.env`, подставьте свой логин вместо `coursework`.

Linux / macOS:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://coursework:coursework_local@localhost:5432/coursework_test
python -m pytest -q --cov=app --cov=scripts.seed_demo --cov-report=term-missing
ruff check .
```

Windows PowerShell:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://coursework:coursework_local@localhost:5432/coursework_test"
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov=scripts.seed_demo --cov-report=term-missing
.\.venv\Scripts\ruff.exe check .
```

`TEST_DATABASE_URL` задается в окружении терминала; pytest не загружает его из `.env`.
Каждый тест создает отдельную схему `test_<uuid>`, применяет миграции и удаляет только
эту схему. Схема `public` исключена из `search_path` тестового соединения.
Тестовый пользователь должен иметь право `CREATE SCHEMA`.
Отсутствие `TEST_DATABASE_URL` считается ошибкой, тесты БД не пропускаются молча.

Результаты поставляемой версии: [docs/test_report.md](docs/test_report.md),
JUnit XML и JSON покрытия находятся рядом.

## 6. Документация и структура

```text
app/                         конфигурация, сессия БД, ORM-модели, каркас FastAPI
alembic/versions/            обратимые версионные миграции
scripts/seed_demo.py         транзакционная загрузка учебного набора
scripts/export_schema.py     словарь и ERD из физической PostgreSQL-схемы
tests/                      интеграционные тесты PostgreSQL и проверки API
docs/design.md              предметная область, связи и ограничения текущего этапа
docs/requirements_review.md  анализ предоставленных документов
docs/data_dictionary.md     все поля, типы, PK/FK, CHECK, UNIQUE, индексы
docs/erd.svg, docs/erd.pdf   физическая ER-диаграмма для просмотра и печати
docs/erd.dot, schema.json    исходные сведения диаграммы и словаря
docs/migrations.sql         SQL миграций 0001 и 0002
docs/stage1_report.docx      краткая пояснительная записка по выполненному этапу
docs/test_report.md          план и фактические результаты проверки
compose.yaml                локальный сервер PostgreSQL
.env.example                образец настроек без индивидуальных секретов
requirements*.txt, .lock     проверенные зависимости
```

Для пересоздания диаграммы и словаря нужна примененная схема; для рендеринга — Graphviz:

```bash
python -m scripts.export_schema
dot -Tsvg docs/erd.dot -o docs/erd.svg
dot -Tpdf docs/erd.dot -o docs/erd.pdf
```

Исходные документы пользователя не дублируются в архиве. Краткая записка описывает
только выполненный этап и не выдается за итоговую пояснительную записку на 40–60 страниц.
