import os
import tempfile

os.environ["ENVIRONMENT"] = "test"
os.environ["OBJECT_STORAGE_BACKEND"] = "local"
os.environ["OBJECT_STORAGE_LOCAL_DIR"] = tempfile.mkdtemp(prefix="clic-os-test-")
os.environ["API_B_BASE_URL"] = ""
os.environ["API_C_BASE_URL"] = ""
os.environ["INTEGRATION_STUB_WHEN_UNREACHABLE"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.storage.factory import get_object_storage


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    get_object_storage.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_object_storage.cache_clear()
