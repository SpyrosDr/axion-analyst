# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    # bcrypt only hashes the first 72 bytes; cap length here (plus a byte-level
    # guard in user_service for multi-byte characters).
    password: str = Field(min_length=8, max_length=72)
    is_admin: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool
    created_at: datetime
    display_name: str | None = None
    avatar_url: str | None = None
    avatar_color: str | None = None
    global_role: str = "none"


class UserSummary(BaseModel):
    """Shape for the collaborator picker and case owner/collaborator display --
    no is_admin/created_at/global_role leak (permission metadata stays
    admin-only via GET /auth/users/detailed), but includes profile fields
    since those are already public-within-the-app, same trust level as
    username."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    avatar_color: str | None = None


class UserRoleUpdate(BaseModel):
    global_role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)


class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = None
    avatar_color: str | None = None
