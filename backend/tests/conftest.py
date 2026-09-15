import os

os.environ["TRIVIA_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["TRIVIA_MEDIA_ROOT"] = "/tmp/trivia-forge-test-media"
os.environ["TRIVIA_SEED_ON_START"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_database


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
