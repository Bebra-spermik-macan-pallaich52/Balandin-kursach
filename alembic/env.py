from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.config import get_settings
from app.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def run_with_connection(connection):
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=get_settings().database_url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    # В тестах используется соединение с отдельной временной схемой.
    run_with_connection(config.attributes["connection"])
else:
    engine = create_engine(
        get_settings().database_url, poolclass=pool.NullPool, hide_parameters=True
    )
    with engine.connect() as connection:
        run_with_connection(connection)
    engine.dispose()
