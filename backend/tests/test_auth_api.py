import pytest
from app.models.models import User
from app.core.auth import hash_password, create_access_token


def test_login_success_and_jwt_issuance(unauth_client, db_session):
    """Verify authenticating with correct credentials returns 200, JWT token and user profile."""
    res = unauth_client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password_returns_401(unauth_client, db_session):
    """Verify incorrect password returns 401 Unauthorized."""
    res = unauth_client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]


def test_login_nonexistent_user_returns_401(unauth_client, db_session):
    """Verify non-existent username returns 401 Unauthorized."""
    res = unauth_client.post("/api/v1/auth/login", json={
        "username": "ghost_user",
        "password": "password"
    })
    assert res.status_code == 401


def test_get_current_user_me(unauth_client, auth_headers):
    """Verify /api/v1/auth/me returns identity of authenticated caller."""
    headers = auth_headers("quality_lead", "quality_lead")
    res = unauth_client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["username"] == "quality_lead"
    assert res.json()["role"] == "quality_lead"


def test_get_current_user_me_unauthenticated_returns_401(unauth_client):
    """Verify unauthenticated call to /api/v1/auth/me returns 401."""
    res = unauth_client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_register_new_user(unauth_client, db_session):
    """Verify registering a new user creates account with hashed password."""
    res = unauth_client.post("/api/v1/auth/register", json={
        "username": "engineer_chen",
        "email": "chen@eql-auto.internal",
        "password": "SecretPass2026!",
        "full_name": "Dr. Chen",
        "role": "design_engineer",
        "department": "Door Structures"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "engineer_chen"
    assert data["role"] == "design_engineer"

    # Confirm user can log in with new credentials
    login_res = unauth_client.post("/api/v1/auth/login", json={
        "username": "engineer_chen",
        "password": "SecretPass2026!"
    })
    assert login_res.status_code == 200


def test_duplicate_registration_rejected(unauth_client, db_session):
    """Verify registering duplicate username returns 409 Conflict."""
    res = unauth_client.post("/api/v1/auth/register", json={
        "username": "admin",  # Already exists
        "email": "different_email@test.local",
        "password": "Password123!",
        "full_name": "Duplicate Admin",
        "role": "viewer"
    })
    assert res.status_code == 409


def test_admin_list_users_rbac(unauth_client, auth_headers):
    """Verify only admin can query /api/v1/auth/users; viewer gets 403."""
    admin_headers = auth_headers("admin", "admin")
    res_admin = unauth_client.get("/api/v1/auth/users", headers=admin_headers)
    assert res_admin.status_code == 200
    assert len(res_admin.json()) >= 4

    viewer_headers = auth_headers("auditor", "viewer")
    res_viewer = unauth_client.get("/api/v1/auth/users", headers=viewer_headers)
    assert res_viewer.status_code == 403
