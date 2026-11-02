"""Словарь данных и исходник ERD из физической схемы PostgreSQL.

python -m scripts.export_schema
dot -Tsvg docs/erd.dot -o docs/erd.svg
dot -Tpdf docs/erd.dot -o docs/erd.pdf
"""

import html
import json
from pathlib import Path

from sqlalchemy import inspect

from app.database import get_engine


def main() -> None:
    inspector = inspect(get_engine())
    docs = Path(__file__).resolve().parents[1] / "docs"
    docs.mkdir(exist_ok=True)
    dictionary = [
        "# Словарь данных PostgreSQL",
        "",
        "Сформирован из примененной схемы, включая PK, FK, UNIQUE, CHECK и индексы.",
        "UQ — уникальность одного поля; UQ* — участие в составном UNIQUE (паспорт).",
        "Таблица alembic_version является служебной и в предметную модель не входит.",
        "Временные метки — TIMESTAMP WITH TIME ZONE; отображение задается часовым поясом клиента.",
        "",
    ]
    dot = [
        "digraph ERD {",
        'graph [rankdir=LR, bgcolor="white", pad="0.3", nodesep=0.6, ranksep=1.4];',
        'node [shape=plain, fontname="DejaVu Sans", fontsize=10];',
        'edge [color="#52708a", fontname="DejaVu Sans", fontsize=8];',
    ]
    schema = []
    for table in inspector.get_table_names():
        if table == "alembic_version":
            continue
        pk = inspector.get_pk_constraint(table)["constrained_columns"]
        fks = inspector.get_foreign_keys(table)
        unique = inspector.get_unique_constraints(table)
        indexes = inspector.get_indexes(table)
        checks = inspector.get_check_constraints(table)
        foreign_columns = {c for fk in fks for c in fk["constrained_columns"]}
        uq_columns = {uq["column_names"][0] for uq in unique if len(uq["column_names"]) == 1}
        composite_uq_columns = {
            c for uq in unique if len(uq["column_names"]) > 1 for c in uq["column_names"]
        }
        comment = inspector.get_table_comment(table)["text"]
        dictionary += [
            f"## {table}",
            "",
            comment or "",
            "",
            "| Ключ | Поле | PostgreSQL | NULL | По умолчанию | Назначение |",
            "|---|---|---|---|---|---|",
        ]
        rows = []
        fields = []
        for column in inspector.get_columns(table):
            name = column["name"]
            keys = []
            if name in pk:
                keys.append("PK")
            if name in foreign_columns:
                keys.append("FK")
            if name in uq_columns:
                keys.append("UQ")
            if name in composite_uq_columns:
                keys.append("UQ*")
            default = "IDENTITY" if column.get("identity") else str(column.get("default") or "—")
            data_type = str(column["type"])
            if getattr(column["type"], "timezone", False):
                data_type += " WITH TIME ZONE"
            description = column.get("comment") or ""
            nullable = "Да" if column["nullable"] else "Нет"
            dictionary.append(
                f"| {', '.join(keys) or '—'} | `{name}` | {data_type} | {nullable} | "
                f"{default} | {description} |"
            )
            fields.append(
                dict(
                    name=name,
                    keys=keys,
                    type=data_type,
                    nullable=column["nullable"],
                    default=default,
                    description=description,
                )
            )
            label = html.escape(f"{','.join(keys):7} {name}: {data_type}")
            rows.append(f'<TR><TD ALIGN="LEFT">{label}</TD></TR>')
        dictionary += ["", "Внешние ключи:", ""]
        if not fks:
            dictionary += ["Нет."]
        for fk in fks:
            dictionary.append(
                f"- `{','.join(fk['constrained_columns'])}` → `{fk['referred_table']}."
                f"{','.join(fk['referred_columns'])}`, ON DELETE "
                f"{fk['options'].get('ondelete', 'NO ACTION')}."
            )
            columns = set(fk["constrained_columns"])
            to_one = columns == set(pk) or any(columns == set(uq["column_names"]) for uq in unique)
            cardinality = "1:0..1" if to_one else "1:0..N"
            arrow = "tee" if to_one else "crow"
            dot.append(
                f'"{fk["referred_table"]}" -> "{table}" '
                f'[label="{",".join(fk["constrained_columns"])} ({cardinality})", '
                f"arrowhead={arrow}];"
            )
        dictionary += ["", "Ограничения и индексы:", ""]
        for uq in unique:
            dictionary.append(f"- UNIQUE `{uq['name']}`: {', '.join(uq['column_names'])}.")
        for check in checks:
            dictionary.append(f"- CHECK `{check['name']}`: `{check['sqltext']}`.")
        for index in indexes:
            expression = index.get("expressions") or index["column_names"]
            dictionary.append(f"- INDEX `{index['name']}`: {expression}; unique={index['unique']}.")
        dictionary += [""]
        dot.append(
            f'"{table}" [label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" '
            f'CELLPADDING="5"><TR><TD BGCOLOR="#183b56"><FONT COLOR="white">'
            f"<B>{table}</B></FONT></TD></TR>{''.join(rows)}</TABLE>>];"
        )
        schema.append(
            dict(
                table=table,
                comment=comment,
                fields=fields,
                foreign_keys=fks,
                unique=unique,
                indexes=indexes,
                checks=checks,
            )
        )
    dot.append("}")
    (docs / "data_dictionary.md").write_text("\n".join(dictionary), encoding="utf-8")
    (docs / "erd.dot").write_text("\n".join(dot), encoding="utf-8")
    (docs / "schema.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Созданы docs/data_dictionary.md, docs/erd.dot и docs/schema.json")


if __name__ == "__main__":
    main()
