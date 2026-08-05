# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import ACCESS_TOKEN_COOKIE_NAME, decode_access_token
from app.database.db import get_db
from app.models.case import Case
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.services import case_service, permissions

# auto_error=False: a missing header isn't fatal here, since the browser
# frontend authenticates via the httpOnly cookie instead (_extract_token
# below falls back to it). API clients/tools may keep using the header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _extract_token(
    request: Request, header_token: str | None = Depends(oauth2_scheme)
) -> str | None:
    """`Authorization: Bearer` header wins if present (API clients, tests,
    Swagger UI); otherwise falls back to the httpOnly session cookie the
    browser frontend sends automatically."""
    return header_token or request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)


def get_current_token_payload(
    token: str | None = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> dict:
    if token is None:
        raise _credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception

    jti = payload.get("jti")
    if jti and db.query(RevokedToken.jti).filter(RevokedToken.jti == jti).first():
        # Token is otherwise valid but was explicitly logged out.
        raise _credentials_exception

    return payload


def get_current_user(
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise _credentials_exception from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _credentials_exception

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user


def viewable_case(
    case_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Case:
    """Resolves the {case_id} path param to a case the requester may view
    (404 otherwise), with my_role pre-computed for response serialization.
    Every /cases/{case_id}/... route goes through this or editable_case, so
    access control is structural rather than per-route boilerplate."""
    case = case_service.get_case_or_404(db, case_id, user)
    case.my_role = permissions.effective_role(case, user)
    return case


def editable_case(
    case: Case = Depends(viewable_case),
    user: User = Depends(get_current_user),
) -> Case:
    case_service.require_edit(case, user)
    return case


def managed_case(
    case: Case = Depends(viewable_case),
    user: User = Depends(get_current_user),
) -> Case:
    case_service.require_manage(case, user)
    return case
