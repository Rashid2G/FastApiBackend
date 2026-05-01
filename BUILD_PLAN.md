# FastAPI Secure Backend Build Plan

## Objective

Build a Python FastAPI backend that demonstrates secure authentication with JWTs, bcrypt password hashing, role-based access control, token revocation, and defensive security logging.

## Technology Stack

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Password Hashing:** direct `bcrypt`
- **JWT Handling:** PyJWT
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Testing:** pytest and FastAPI TestClient

## Project Structure

```text
FastApiBackend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── dependencies.py
│   └── logging_config.py
├── tests/
│   ├── test_auth.py
│   └── test_authorization.py
├── .env.example
├── security.log
├── requirements.txt
├── README.md
├── BUILD_PLAN.md
└── REPORT.md
```

## Implementation Steps

### 1. Initialize FastAPI Project

- Create the `app/` package.
- Add `main.py` with the FastAPI application instance.
- Add health check route:

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### 2. Configure SQLite Database

- Use SQLite for local persistence.
- Create a `users` table with:
  - `id`
  - `username`
  - `hashed_password`
  - `role`
  - `created_at`

The password column must store only a bcrypt hash, never the original password.

### 3. Implement Registration

Endpoint:

```http
POST /register
```

Request body:

```json
{
  "username": "alice",
  "password": "StrongPassword123!",
  "role": "user"
}
```

Rules:

- Hash the password with bcrypt before storage.
- Default role should be `user`.
- Reject duplicate usernames.
- Prevent normal public registration from creating an admin account unless an explicit seed/admin setup path is used.

Security decision:

- Admin users should be seeded manually or created through an admin-only route, not through unrestricted registration.

### 4. Implement Login and JWT Issuance

Endpoint:

```http
POST /login
```

Request body:

```json
{
  "username": "alice",
  "password": "StrongPassword123!"
}
```

Successful response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

JWT payload should contain:

```json
{
  "sub": "alice",
  "role": "user",
  "exp": 1710000000,
  "iat": 1709996400,
  "jti": "unique-token-id"
}
```

Notes:

- `sub` identifies the authenticated user.
- `role` supports authorization decisions.
- `exp` enforces expiry.
- `jti` supports logout blacklisting.

### 5. Implement Token Validation

Create a reusable dependency that:

- Reads the `Authorization` header.
- Requires the `Bearer <token>` format.
- Decodes and verifies the JWT.
- Rejects expired or invalid tokens.
- Checks whether the token `jti` is blacklisted.
- Loads the current user from the database.

Protected routes should use this dependency.

### 6. Implement Role-Based Access Control

Protected user route:

```http
GET /profile
```

Access:

- `user`
- `admin`

Protected admin route:

```http
DELETE /user/{id}
```

Access:

- `admin` only

Authorization rules:

- A standard user must receive `403 Forbidden` when attempting to call admin-only routes.
- Missing, expired, revoked, or malformed tokens should receive `401 Unauthorized`.
- Valid tokens with insufficient role permissions should receive `403 Forbidden`.

### 7. Implement Logout and Token Blacklisting

Endpoint:

```http
POST /logout
```

Behavior:

- Requires a valid JWT.
- Extracts the token `jti`.
- Stores the `jti` in an in-memory blacklist or database table.
- Future requests using that same token must be rejected.

Recommended implementation:

- For assignment simplicity: in-memory `set`.
- For stronger persistence: SQLite `blacklisted_tokens` table.

### 8. Implement Defensive Logging

Create exception handling that logs every `403 Forbidden` authorization failure to `security.log`.

Log format:

```text
2026-05-01T15:30:00+03:00 | 403 Forbidden | user=alice | method=DELETE | path=/user/2
```

Required logged fields:

- Timestamp
- HTTP method
- Attempted path/action
- Username when available
- Reason for denial

### 9. Add Tests

Minimum test cases:

- Register stores hashed password, not plaintext.
- Login succeeds with correct credentials.
- Login fails with wrong password.
- `/profile` works for `user`.
- `/profile` works for `admin`.
- `DELETE /user/{id}` fails for `user` with `403`.
- `DELETE /user/{id}` works for `admin`.
- Logout revokes token.
- Revoked token cannot access protected routes.
- Unauthorized admin attempt writes to `security.log`.

### 10. Documentation and Submission

Include:

- `README.md` with setup and run commands.
- `REPORT.md` with the required security explanations.
- API route list.
- Example request bodies.
- Notes about least privilege and JWT safety.

## Milestones

1. Completed: Create project structure and dependencies.
2. Completed: Add database models and startup table creation.
3. Completed: Add password hashing and registration.
4. Completed: Add login and JWT issuance.
5. Completed: Add authentication dependency.
6. Completed: Add role-based protected routes.
7. Completed: Add logout blacklist.
8. Completed: Add forbidden-attempt logging.
9. Completed: Add tests.
10. Completed: Finalize documentation.

## Acceptance Criteria

- Passwords are stored as bcrypt hashes only.
- JWTs include username and role.
- Expired, invalid, and revoked tokens are rejected.
- `/profile` is available to both roles.
- `DELETE /user/{id}` is available only to admins.
- Standard users cannot access admin functionality.
- Logout invalidates the active token.
- `403 Forbidden` attempts are logged to `security.log`.
- Documentation explains salting and JWT sensitive-data risks.
