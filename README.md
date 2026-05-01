# FastAPI Secure Backend

This project is a FastAPI backend for secure authentication and role-based authorization using JWTs, bcrypt password hashing, token blacklisting, and defensive logging.

## Features

- User registration with bcrypt password hashing
- Login endpoint that issues signed JWT access tokens
- Protected route authentication using the `Authorization: Bearer <token>` header
- Role-based authorization for `user` and `admin`
- Logout endpoint with JWT blacklist support
- Security logging for forbidden admin-access attempts
- SQLite persistence through SQLAlchemy

## Planned API Routes

| Method | Route | Access | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | Public | Health check |
| `POST` | `/register` | Public | Register a standard user |
| `POST` | `/login` | Public | Authenticate and receive JWT |
| `GET` | `/profile` | User/Admin | View current user profile |
| `POST` | `/logout` | User/Admin | Revoke current JWT |
| `DELETE` | `/user/{id}` | Admin only | Delete a user |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## Dependencies

```text
fastapi
uvicorn[standard]
sqlalchemy
pydantic
PyJWT
bcrypt
python-dotenv
pytest
httpx
```

Note: this FastAPI implementation uses the `bcrypt` package directly for password hashing. `Flask-Bcrypt` is Flask-specific.

## Example Requests

### Register

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"StrongPassword123!"}'
```

Public registration creates standard users by default.

### Register Admin

Set `ADMIN_REGISTRATION_KEY` in `.env`, then send the matching header:

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -H "X-Admin-Registration-Key: replace-with-a-temporary-admin-registration-key" \
  -d '{"username":"root","password":"AdminPassword123!","role":"admin"}'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"StrongPassword123!"}'
```

### Profile

```bash
curl http://127.0.0.1:8000/profile \
  -H "Authorization: Bearer <token>"
```

### Logout

```bash
curl -X POST http://127.0.0.1:8000/logout \
  -H "Authorization: Bearer <token>"
```

### Delete User as Admin

```bash
curl -X DELETE http://127.0.0.1:8000/user/2 \
  -H "Authorization: Bearer <admin-token>"
```

## Authorization Behavior

- Missing or invalid token: `401 Unauthorized`
- Expired token: `401 Unauthorized`
- Revoked token: `401 Unauthorized`
- Valid token with insufficient role: `403 Forbidden`

Every `403 Forbidden` authorization failure should be logged to `security.log`.

## Documentation

- [Build Plan](BUILD_PLAN.md)
- [Security Report](REPORT.md)
- [Postman Collection](FastAPI_Secure_Backend.postman_collection.json)

## Postman Demo

Import `FastAPI_Secure_Backend.postman_collection.json` into Postman and run the requests in order.

The collection demonstrates:

- Successful Login: a standard user logs in and receives a JWT.
- Access Denied: the standard user calls `DELETE /user/{id}` and receives `403 Forbidden`.
- Tamper Test: the JWT payload role is changed to `admin` without resigning, and the server rejects it with `401 Unauthorized`.

## Tests

```bash
source .venv/bin/activate
pytest -q
```

Current test coverage verifies:

- Passwords are stored as bcrypt hashes.
- Login issues JWTs with username, role, expiry, and token ID.
- User and admin access `/profile`.
- Standard users cannot call admin-only delete routes.
- Admin users can delete standard users.
- Logout revokes the active token.
- Forbidden attempts are written to `security.log`.
