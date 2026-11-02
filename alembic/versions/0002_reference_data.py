"""Роли из ТЗ и состояния kanban-доски.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    roles = sa.table("roles", sa.column("code", sa.String), sa.column("name", sa.String))
    statuses = sa.table(
        "task_statuses",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        roles,
        [
            {"code": "admin", "name": "Администратор"},
            {"code": "director", "name": "Руководитель предприятия"},
            {"code": "department_head", "name": "Руководитель подразделения"},
            {"code": "employee", "name": "Работник"},
        ],
    )
    op.bulk_insert(
        statuses,
        [
            {"code": "new", "name": "Назначена", "sort_order": 1},
            {"code": "in_progress", "name": "В работе", "sort_order": 2},
            {"code": "done", "name": "Выполнена", "sort_order": 3},
            {"code": "cancelled", "name": "Отменена", "sort_order": 4},
        ],
    )


def downgrade() -> None:
    # При наличии связанных данных RESTRICT остановит откат и сохранит целостность.
    op.execute("DELETE FROM task_statuses WHERE code IN ('new','in_progress','done','cancelled')")
    op.execute("DELETE FROM roles WHERE code IN ('admin','director','department_head','employee')")
