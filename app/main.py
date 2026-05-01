from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import blacklist_token, create_access_token, decode_token, hash_password, verify_password
from app.config import ADMIN_REGISTRATION_KEY
from app.database import Base, engine, get_db
from app.dependencies import bearer_scheme, get_current_user, require_admin
from app.logging_config import log_forbidden_attempt
from app.models import User
from app.schemas import LoginRequest, MessageResponse, RegisterRequest, TokenResponse, UserResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure FastAPI Backend")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        log_forbidden_attempt(
            username=getattr(request.state, "username", "unknown"),
            method=request.method,
            path=request.url.path,
            reason=str(exc.detail),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: RegisterRequest,
    x_admin_registration_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    requested_role = user_data.role
    if requested_role == "admin" and (
        not ADMIN_REGISTRATION_KEY or x_admin_registration_key != ADMIN_REGISTRATION_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed",
        )

    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=requested_role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == credentials.username).first()
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return TokenResponse(access_token=create_access_token(user))


@app.get("/profile", response_model=UserResponse)
def profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.post("/logout", response_model=MessageResponse)
def logout(
    credentials=Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    payload = decode_token(credentials.credentials)
    blacklist_token(db, payload)
    return MessageResponse(message=f"Token revoked for {current_user.username}")


@app.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete their own account",
        )

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
