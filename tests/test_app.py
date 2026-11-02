from fastapi.testclient import TestClient

from app.database import get_session
from app.main import app


def test_liveness_and_openapi():
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        schema = client.get("/openapi.json").json()
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v2/health" in schema["paths"]


def test_database_health(database):
    from sqlalchemy.orm import Session

    def override():
        with Session(database[0]) as session:
            yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            for version in ("v1", "v2"):
                assert client.get(f"/api/{version}/health").json() == {
                    "status": "ok",
                    "database": "ok",
                    "api_version": version,
                }
    finally:
        app.dependency_overrides.clear()


def test_database_error_is_503():
    from sqlalchemy.exc import OperationalError

    class BrokenSession:
        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, Exception("not available"))

    app.dependency_overrides[get_session] = lambda: BrokenSession()
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 503
            assert "not available" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_missing_migration_is_503(database):
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with database[0].begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num='0001'"))

    def override():
        with Session(database[0]) as session:
            yield session

    app.dependency_overrides[get_session] = override
    try:
        with TestClient(app) as client:
            assert client.get("/api/v2/health").status_code == 503
    finally:
        app.dependency_overrides.clear()
