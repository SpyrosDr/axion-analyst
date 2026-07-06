from app.models.case import Case
from app.models.user import User

NONE = "none"
VIEWER = "viewer"
EDITOR = "editor"
MANAGER = "manager"

_RANK = {NONE: 0, VIEWER: 1, EDITOR: 2, MANAGER: 3}

ALLOWED_GLOBAL_ROLES = {NONE, VIEWER, EDITOR, MANAGER}
ALLOWED_CASE_ROLES = {VIEWER, EDITOR, MANAGER}


def _rank(role: str | None) -> int:
    # Unknown values (e.g. a NULL left behind by a hand-migrated database)
    # rank as "none" rather than raising.
    return _RANK.get(role, 0)


def has_global_access(user: User) -> bool:
    """Whether the user can see every case, regardless of ownership/sharing."""
    return user.is_admin or _rank(user.global_role) > 0


def effective_role(case: Case, user: User) -> str:
    """The user's strongest grant wins: owner/admin means manager, otherwise
    the higher of their global role and their per-case collaborator role."""
    if case.owner_id == user.id or user.is_admin:
        return MANAGER
    link_role = next(
        (link.role for link in case.collaborator_links if link.user_id == user.id),
        NONE,
    )
    if _rank(link_role) >= _rank(user.global_role):
        return link_role
    return user.global_role


def can_view(role: str) -> bool:
    return _rank(role) >= _RANK[VIEWER]


def can_edit(role: str) -> bool:
    return _rank(role) >= _RANK[EDITOR]


def can_manage(role: str) -> bool:
    return _rank(role) >= _RANK[MANAGER]
