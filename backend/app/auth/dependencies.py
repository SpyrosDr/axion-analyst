# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database.db import get_db
from app.models.case import Case
from app.models.user import User
from app.services import case_service, permissions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_exception

    try:
        user_id = int(subject)
    except ValueError:
        raise credentials_exception from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

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
