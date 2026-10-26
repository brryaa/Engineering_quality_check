import sys
import os

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
real_backend = "/home/brrr/agy/backend"
if real_backend not in sys.path:
    sys.path.append(real_backend)

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.core.auth import get_current_user, hash_password, create_access_token
from app.models.models import User
from app.main import app

# Use StaticPool so all threads/sessions share the same in-memory SQLite database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Pre-populate RBAC test accounts
    users = [
        User(id=1, username="admin", email="admin@test.local", hashed_password=hash_password("admin123"), full_name="Admin User", role="admin", is_active=True),
        User(id=2, username="quality_lead", email="quality@test.local", hashed_password=hash_password("quality123"), full_name="Quality Lead", role="quality_lead", is_active=True),
        User(id=3, username="design_eng", email="design@test.local", hashed_password=hash_password("design123"), full_name="Design Engineer", role="design_engineer", is_active=True),
        User(id=4, username="auditor", email="auditor@test.local", hashed_password=hash_password("auditor123"), full_name="Auditor User", role="viewer", is_active=True),
    ]
    db.add_all(users)
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    admin_user = db_session.query(User).filter_by(username="admin").first()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def unauth_client(db_session):
    """Client without get_current_user override to test raw authentication failures."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def auth_headers():
    """Generates valid JWT bearer Authorization header for specific user."""
    def _headers(username: str, role: str = "viewer"):
        token = create_access_token(data={"sub": username, "role": role})
        return {"Authorization": f"Bearer {token}"}
    return _headers
