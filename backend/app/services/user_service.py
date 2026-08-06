# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user_schema import ProfileUpdate, UserCreate
from app.services import permissions

# Must match frontend/src/components/Avatar.jsx's AVATAR_COLORS exactly --
# this is the fixed "basic colors" palette users can pick an avatar color from.
ALLOWED_AVATAR_COLORS = {
    "#5b3df0",
    "#0f766e",
    "#b45309",
    "#be185d",
    "#1d4ed8",
    "#15803d",
    "#9333ea",
    "#b91c1c",
}


def _check_password_byte_length(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        # bcrypt rejects inputs over 72 bytes; multi-byte characters can
        # exceed that even within a 72-character schema limit.
        raise HTTPException(
            status_code=400, detail="Password may be at most 72 bytes"
        )


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    if get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    _check_password_byte_length(user_in.password)

    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        is_admin=user_in.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username).all()


def update_global_role(db: Session, user_id: int, global_role: str) -> User:
    if global_role not in permissions.ALLOWED_GLOBAL_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.global_role = global_role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> User:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    _check_password_byte_length(new_password)

    user.hashed_password = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_profile(db: Session, user: User, update: ProfileUpdate) -> User:
    if update.username is not None and update.username != user.username:
        existing = get_user_by_username(db, update.username)
        if existing is not None:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = update.username

    if update.display_name is not None:
        user.display_name = update.display_name or None

    if update.avatar_url is not None:
        if update.avatar_url and not update.avatar_url.startswith(
            ("http://", "https://")
        ):
            raise HTTPException(
                status_code=400,
                detail="Avatar URL must start with http:// or https://",
            )
        user.avatar_url = update.avatar_url or None

    if update.avatar_color is not None:
        if update.avatar_color and update.avatar_color not in ALLOWED_AVATAR_COLORS:
            raise HTTPException(status_code=400, detail="Invalid avatar color")
        user.avatar_color = update.avatar_color or None

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
