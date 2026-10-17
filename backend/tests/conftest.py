import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def enable_fk(connection, _): connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    Local = sessionmaker(bind=engine, expire_on_commit=False)
    def override():
        with Local() as db: yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client: yield client
    app.dependency_overrides.clear()
    engine.dispose()
