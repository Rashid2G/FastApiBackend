from pathlib import Path


def create_user(client, username, password, role="user"):
    headers = {}
    if role == "admin":
        headers["X-Admin-Registration-Key"] = "test-admin-key"
    return client.post(
        "/register",
        json={"username": username, "password": password, "role": role},
        headers=headers,
    )


def login(client, username, password):
    return client.post("/login", json={"username": username, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_profile_accessible_by_user_and_admin(client):
    create_user(client, "alice", "StrongPassword123!", "user")
    create_user(client, "root", "AdminPassword123!", "admin")
    user_token = login(client, "alice", "StrongPassword123!").json()["access_token"]
    admin_token = login(client, "root", "AdminPassword123!").json()["access_token"]

    user_response = client.get("/profile", headers=auth_header(user_token))
    admin_response = client.get("/profile", headers=auth_header(admin_token))

    assert user_response.status_code == 200
    assert user_response.json()["role"] == "user"
    assert admin_response.status_code == 200
    assert admin_response.json()["role"] == "admin"


def test_standard_user_cannot_delete_user_and_attempt_is_logged(client):
    create_user(client, "alice", "StrongPassword123!", "user")
    created = create_user(client, "bob", "AnotherPassword123!", "user")
    token = login(client, "alice", "StrongPassword123!").json()["access_token"]

    response = client.delete(f"/user/{created.json()['id']}", headers=auth_header(token))

    assert response.status_code == 403
    log_content = Path("test-security.log").read_text()
    assert "403 Forbidden" in log_content
    assert "user=alice" in log_content
    assert "method=DELETE" in log_content
    assert f"path=/user/{created.json()['id']}" in log_content


def test_admin_can_delete_user(client):
    create_user(client, "root", "AdminPassword123!", "admin")
    created = create_user(client, "bob", "AnotherPassword123!", "user")
    token = login(client, "root", "AdminPassword123!").json()["access_token"]

    response = client.delete(f"/user/{created.json()['id']}", headers=auth_header(token))
    deleted_profile = client.delete(f"/user/{created.json()['id']}", headers=auth_header(token))

    assert response.status_code == 204
    assert deleted_profile.status_code == 404


def test_public_registration_cannot_create_admin_without_setup_key(client):
    response = client.post(
        "/register",
        json={
            "username": "mallory",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 403
