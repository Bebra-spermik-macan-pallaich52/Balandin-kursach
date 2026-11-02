import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("url", ["sqlite:///test.db", "postgresql://localhost/test"])
def test_only_psycopg_postgresql_is_allowed(url):
    with pytest.raises(ValidationError):
        Settings(database_url=url, _env_file=None)


def test_postgresql_config():
    url = "postgresql+psycopg://user:password@localhost:5432/test"
    assert Settings(database_url=url, _env_file=None).database_url == url
