import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.models import User


def register_user(client, username="alice", password="StrongPassword123!"):
    return client.post(
        "/register",
        json={"username": username, "password": password},
    )


def login_user(client, username="alice", password="StrongPassword123!"):
    return client.post(
        "/login",
        json={"username": username, "password": password},
    )


def test_register_stores_hashed_password(client, db_session):
    response = register_user(client)

    assert response.status_code == 201
    user = db_session.query(User).filter(User.username == "alice").one()
    assert user.hashed_password != "StrongPassword123!"
    assert user.hashed_password.startswith("$2")


def test_login_issues_jwt_with_username_and_role(client):
    register_user(client)

    response = login_user(client)

    assert response.status_code == 200
    token = response.json()["access_token"]
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == "alice"
    assert payload["role"] == "user"
    assert "exp" in payload
    assert "jti" in payload


def test_login_rejects_wrong_password(client):
    register_user(client)

    response = login_user(client, password="WrongPassword123!")

    assert response.status_code == 401


def test_logout_revokes_token(client):
    register_user(client)
    token = login_user(client).json()["access_token"]

    logout_response = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    profile_response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})

    assert logout_response.status_code == 200
    assert profile_response.status_code == 401
    assert profile_response.json()["detail"] == "Token has been revoked"
