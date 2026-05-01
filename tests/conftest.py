import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["ADMIN_REGISTRATION_KEY"] = "test-admin-key"
os.environ["SECURITY_LOG_FILE"] = "test-security.log"

from app.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Path("test-security.log").write_text("")
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
