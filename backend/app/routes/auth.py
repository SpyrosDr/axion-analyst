# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import rate_limit
from app.auth.dependencies import get_current_user, require_admin
from app.auth.security import create_access_token
from app.database.db import get_db
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


@router.post("/login", response_model=Token)
def login(
    request: Request,
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
    return Token(access_token=token)


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
