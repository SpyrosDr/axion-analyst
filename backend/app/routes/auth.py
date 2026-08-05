# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import rate_limit
from app.auth.dependencies import get_current_token_payload, get_current_user, require_admin
from app.auth.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.config import settings
from app.database.db import get_db
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.schemas.user_schema import (
    PasswordChange,
    ProfileUpdate,
    Token,
    UserCreate,
    UserResponse,
    UserRoleUpdate,
    UserSummary,
)
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        # Only forces HTTPS in production -- local dev over plain HTTP
        # (Vite on localhost) would otherwise have the cookie silently
        # dropped by the browser.
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        path="/",
    )


@router.post("/login", response_model=Token)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    retry_after = rate_limit.seconds_until_unlocked(form_data.username, client_ip)
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        rate_limit.record_failure(form_data.username, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    rate_limit.record_success(form_data.username, client_ip)
    # The token identifies the user by their permanent id, not username, so
    # a later username change doesn't invalidate outstanding tokens.
    token = create_access_token(subject=str(user.id))
    # The browser frontend authenticates via this httpOnly cookie (never
    # touches the token directly, so it's not exposed to XSS via
    # localStorage/JS). The token is also still returned in the response
    # body for API clients/tools that use the Authorization header instead.
    _set_session_cookie(response, token)
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
):
    """Revokes the current access token server-side (denylisted by jti) and
    clears the session cookie. Without this, logging out only ever
    discarded the token client-side -- a copy captured before logout (XSS,
    a proxy log, a stolen device) stayed valid until it naturally expired."""
    now = datetime.now(timezone.utc)

    # Opportunistic cleanup: entries here can no longer pass JWT validation
    # once their own exp has passed anyway, so there's no reason to keep
    # them -- this keeps the table from growing unboundedly.
    db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete()

    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and not db.query(RevokedToken.jti).filter(RevokedToken.jti == jti).first():
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else now
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()

    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, path="/")
    return None


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return user_service.create_user(db, user_in)


@router.get("/users", response_model=list[UserSummary])
def list_users(
    db: Session = Depends(get_db), _user: User = Depends(get_current_user)
):
    return user_service.list_users(db)


@router.get("/users/detailed", response_model=list[UserResponse])
def list_users_detailed(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
):
    """Admin-only listing that includes permission metadata (is_admin,
    global_role) for the Manage Users screen."""
    return user_service.list_users(db)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return user_service.update_global_role(db, user_id, body.global_role)


@router.put("/me/password", response_model=UserResponse)
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.change_password(
        db, current_user, body.current_password, body.new_password
    )


@router.put("/me", response_model=UserResponse)
def update_profile(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_profile(db, current_user, body)
