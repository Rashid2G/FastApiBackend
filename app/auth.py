from datetime import datetime, timezone
from uuid import uuid4

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRES, JWT_ALGORITHM, JWT_SECRET_KEY
from app.models import BlacklistedToken, User


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user: User) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + ACCESS_TOKEN_EXPIRES
    payload = {
        "sub": user.username,
        "role": user.role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc


def is_token_blacklisted(db: Session, jti: str) -> bool:
    return db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first() is not None


def blacklist_token(db: Session, token_payload: dict) -> None:
    jti = token_payload["jti"]
    if is_token_blacklisted(db, jti):
        return

    expires_at = datetime.fromtimestamp(token_payload["exp"], tz=timezone.utc)
    blacklisted = BlacklistedToken(
        jti=jti,
        username=token_payload["sub"],
        expires_at=expires_at,
    )
    db.add(blacklisted)
    db.commit()
