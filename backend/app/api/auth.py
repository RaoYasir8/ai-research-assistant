from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_csrf
from app.config import settings
from app.db import get_db
from app.models import RefreshSession, User
from app.rate_limit import enforce_rate_limit
from app.schemas import LoginRequest, RegisterRequest, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    new_csrf_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, user_id: str, db: Session) -> None:
    access = create_access_token(user_id)
    refresh, jti, expires = create_refresh_token(user_id)
    csrf = new_csrf_token()
    db.add(RefreshSession(user_id=user_id, jti=jti, expires_at=expires))
    db.commit()
    cookie_common = {
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(
        "access_token",
        access,
        httponly=True,
        max_age=settings.access_token_minutes * 60,
        **cookie_common,
    )
    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        max_age=settings.refresh_token_days * 86400,
        **cookie_common,
    )
    response.set_cookie(
        "csrf_token",
        csrf,
        httponly=False,
        max_age=settings.refresh_token_days * 86400,
        **cookie_common,
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "register", limit=8, window_seconds=60)
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(name=payload.name, email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_auth_cookies(response, user.id, db)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_rate_limit(request, "login", limit=12, window_seconds=60)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    _set_auth_cookies(response, user.id, db)
    return user


@router.post("/refresh")
def refresh(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_csrf),
):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh session missing")
    try:
        payload = decode_token(token, "refresh")
    except InvalidTokenError as exc:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh session expired") from exc

    session = db.scalar(select(RefreshSession).where(RefreshSession.jti == payload["jti"]))
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh session is not valid")

    session.revoked_at = now
    db.commit()
    _set_auth_cookies(response, payload["sub"], db)
    return {"ok": True}


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        try:
            payload = decode_token(token, "refresh")
            session = db.scalar(select(RefreshSession).where(RefreshSession.jti == payload["jti"]))
            if session and session.revoked_at is None:
                session.revoked_at = datetime.now(timezone.utc)
                db.commit()
        except InvalidTokenError:
            pass
    _clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
