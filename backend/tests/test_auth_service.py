import pytest
from fastapi import HTTPException

from backend.schemas.user import UserCreate
from backend.services.auth_service import login_user, register_user


def _payload(username="alice", email="alice@example.com", password="securepassword"):
    return UserCreate(username=username, email=email, password=password)


# --- register_user ---

def test_register_returns_user_out(db):
    out = register_user(_payload(), db)
    assert out.username == "alice"
    assert out.email == "alice@example.com"


def test_register_default_elo_and_stats(db):
    out = register_user(_payload(), db)
    assert out.elo_rating == 1200
    assert out.wins == 0
    assert out.losses == 0


def test_register_assigns_id(db):
    out = register_user(_payload(), db)
    assert out.id is not None and out.id != ""


def test_register_duplicate_username_raises_400(db):
    register_user(_payload(), db)
    with pytest.raises(HTTPException) as exc:
        register_user(_payload(email="other@example.com"), db)
    assert exc.value.status_code == 400


def test_register_duplicate_email_raises_400(db):
    register_user(_payload(username="alice"), db)
    with pytest.raises(HTTPException) as exc:
        register_user(_payload(username="bob"), db)
    assert exc.value.status_code == 400


def test_register_two_distinct_users_succeeds(db):
    out1 = register_user(_payload(username="alice", email="alice@example.com"), db)
    out2 = register_user(_payload(username="bob", email="bob@example.com"), db)
    assert out1.id != out2.id


# --- login_user ---

def test_login_returns_bearer_token(db):
    register_user(_payload(), db)
    token = login_user("alice", "securepassword", db)
    assert token.token_type == "bearer"
    assert token.access_token and len(token.access_token) > 10


def test_login_wrong_password_raises_401(db):
    register_user(_payload(), db)
    with pytest.raises(HTTPException) as exc:
        login_user("alice", "wrongpassword", db)
    assert exc.value.status_code == 401


def test_login_nonexistent_user_raises_401(db):
    with pytest.raises(HTTPException) as exc:
        login_user("nobody", "anypassword", db)
    assert exc.value.status_code == 401


def test_login_case_sensitive_username(db):
    register_user(_payload(username="alice"), db)
    with pytest.raises(HTTPException) as exc:
        login_user("Alice", "securepassword", db)
    assert exc.value.status_code == 401
