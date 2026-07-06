import pytest
from fastapi.testclient import TestClient

from app.database.db import SessionLocal, init_db
from app.main import app
from app.schemas.user_schema import UserCreate
from app.services import user_service

client = TestClient(app)


def _login_as(username: str, password: str, is_admin: bool = False) -> dict:
    init_db()
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, username):
            user_service.create_user(
                db,
                UserCreate(username=username, password=password, is_admin=is_admin),
            )
    finally:
        db.close()

    response = client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _user_id(headers: dict) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


@pytest.fixture
def perm_admin():
    return _login_as("perm-admin", "permadminpass1", is_admin=True)


@pytest.fixture
def perm_owner():
    return _login_as("perm-owner", "permownerpass1")


@pytest.fixture
def perm_global_viewer():
    return _login_as("perm-global-viewer", "permviewerpass1")


@pytest.fixture
def perm_global_editor():
    return _login_as("perm-global-editor", "permeditorpass1")


@pytest.fixture
def perm_global_manager():
    return _login_as("perm-global-manager", "permmanagerpass1")


@pytest.fixture
def perm_case_viewer():
    return _login_as("perm-case-viewer", "permcaseviewpass1")


@pytest.fixture
def perm_case_editor():
    return _login_as("perm-case-editor", "permcaseeditpass1")


@pytest.fixture
def perm_case_manager():
    return _login_as("perm-case-manager", "permcasemgrpass1")


def _create_case(headers: dict) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": "Permission matrix test case",
            "description": "Exercises the tiered role system.",
            # Rich enough for the mock extractor to find entities/dates.
            "evidence_items": [
                "2024-04-05: Invoice #1001 for $9,850.00 from Brightline Supply Co.",
                "Vendor account #55210984 matches employee payroll.",
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _set_global_role(admin_headers, user_headers, role: str):
    user_id = _user_id(user_headers)
    response = client.patch(
        f"/auth/users/{user_id}/role",
        json={"global_role": role},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["global_role"] == role


def _add_case_collaborator(owner_headers, case_id, target_headers, role: str):
    username = client.get("/auth/me", headers=target_headers).json()["username"]
    response = client.post(
        f"/cases/{case_id}/collaborators",
        json={"username": username, "role": role},
        headers=owner_headers,
    )
    assert response.status_code == 200
    return response.json()


def test_global_viewer_can_view_but_not_edit_or_manage(
    perm_admin, perm_owner, perm_global_viewer
):
    case = _create_case(perm_owner)
    _set_global_role(perm_admin, perm_global_viewer, "viewer")

    assert (
        client.get(f"/cases/{case['id']}", headers=perm_global_viewer).status_code
        == 200
    )
    listed_ids = [
        c["id"] for c in client.get("/cases", headers=perm_global_viewer).json()
    ]
    assert case["id"] in listed_ids

    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "should be blocked"},
            headers=perm_global_viewer,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/cases/{case['id']}/risk-assessment", headers=perm_global_viewer
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/cases/{case['id']}/report", headers=perm_global_viewer
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/cases/{case['id']}/collaborators",
            json={"username": "perm-owner", "role": "viewer"},
            headers=perm_global_viewer,
        ).status_code
        == 403
    )


def test_global_editor_can_edit_but_not_manage(
    perm_admin, perm_owner, perm_global_editor
):
    case = _create_case(perm_owner)
    _set_global_role(perm_admin, perm_global_editor, "editor")

    assert (
        client.get(f"/cases/{case['id']}", headers=perm_global_editor).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "added by global editor"},
            headers=perm_global_editor,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{case['id']}/risk-assessment", headers=perm_global_editor
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{case['id']}/collaborators",
            json={"username": "perm-owner", "role": "viewer"},
            headers=perm_global_editor,
        ).status_code
        == 403
    )


def test_global_manager_can_manage_collaborators_on_unowned_case(
    perm_admin, perm_owner, perm_global_manager, perm_case_viewer
):
    case = _create_case(perm_owner)
    _set_global_role(perm_admin, perm_global_manager, "manager")

    added = _add_case_collaborator(
        perm_global_manager, case["id"], perm_case_viewer, "viewer"
    )
    assert added["role"] == "viewer"

    target_id = _user_id(perm_case_viewer)
    response = client.patch(
        f"/cases/{case['id']}/collaborators/{target_id}",
        json={"role": "editor"},
        headers=perm_global_manager,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "editor"

    assert (
        client.delete(
            f"/cases/{case['id']}/collaborators/{target_id}",
            headers=perm_global_manager,
        ).status_code
        == 204
    )


def test_per_case_viewer_role(perm_owner, perm_case_viewer):
    case = _create_case(perm_owner)
    _add_case_collaborator(perm_owner, case["id"], perm_case_viewer, "viewer")

    assert (
        client.get(f"/cases/{case['id']}", headers=perm_case_viewer).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "blocked"},
            headers=perm_case_viewer,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/cases/{case['id']}/collaborators",
            json={"username": "perm-owner", "role": "viewer"},
            headers=perm_case_viewer,
        ).status_code
        == 403
    )


def test_per_case_editor_role(perm_owner, perm_case_editor):
    case = _create_case(perm_owner)
    _add_case_collaborator(perm_owner, case["id"], perm_case_editor, "editor")

    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "added by case editor"},
            headers=perm_case_editor,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/cases/{case['id']}/collaborators",
            json={"username": "perm-owner", "role": "viewer"},
            headers=perm_case_editor,
        ).status_code
        == 403
    )


def test_per_case_manager_role_can_manage_but_not_delete(
    perm_owner, perm_case_manager, perm_case_viewer
):
    case = _create_case(perm_owner)
    _add_case_collaborator(perm_owner, case["id"], perm_case_manager, "manager")

    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "added by case manager"},
            headers=perm_case_manager,
        ).status_code
        == 200
    )

    added = _add_case_collaborator(
        perm_case_manager, case["id"], perm_case_viewer, "viewer"
    )
    assert added["role"] == "viewer"

    # Managing collaborators is allowed, but deleting the case is still
    # owner-only regardless of role.
    assert (
        client.delete(f"/cases/{case['id']}", headers=perm_case_manager).status_code
        == 403
    )


def test_admin_has_implicit_manager_access_without_global_role(perm_admin, perm_owner):
    case = _create_case(perm_owner)

    me = client.get("/auth/me", headers=perm_admin).json()
    assert me["global_role"] == "none"

    assert client.get(f"/cases/{case['id']}", headers=perm_admin).status_code == 200
    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "added by admin"},
            headers=perm_admin,
        ).status_code
        == 200
    )
    listed_ids = [c["id"] for c in client.get("/cases", headers=perm_admin).json()]
    assert case["id"] in listed_ids


def test_owner_keeps_full_rights_regardless_of_own_global_role(
    perm_admin, perm_owner
):
    case = _create_case(perm_owner)
    _set_global_role(perm_admin, perm_owner, "viewer")

    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "owner still has full rights"},
            headers=perm_owner,
        ).status_code
        == 200
    )
    assert (
        client.delete(f"/cases/{case['id']}", headers=perm_owner).status_code == 204
    )
    _set_global_role(perm_admin, perm_owner, "none")


def test_per_case_grant_beats_lower_global_role(
    perm_admin, perm_owner, perm_case_editor
):
    case = _create_case(perm_owner)
    _add_case_collaborator(perm_owner, case["id"], perm_case_editor, "editor")
    # A weaker global role must not downgrade the explicit per-case grant.
    _set_global_role(perm_admin, perm_case_editor, "viewer")

    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "", "type": "", "content": "per-case editor wins"},
            headers=perm_case_editor,
        ).status_code
        == 200
    )
    detail = client.get(f"/cases/{case['id']}", headers=perm_case_editor).json()
    assert detail["my_role"] == "editor"

    # Reset so other tests see this user without a global role.
    _set_global_role(perm_admin, perm_case_editor, "none")


def test_entities_and_timeline_gets_are_read_only(perm_owner, perm_case_viewer):
    case = _create_case(perm_owner)
    _add_case_collaborator(perm_owner, case["id"], perm_case_viewer, "viewer")

    # Nothing has been generated yet -- the GETs must return empty lists,
    # not trigger generation (which writes rows and can call the AI).
    assert (
        client.get(
            f"/cases/{case['id']}/entities", headers=perm_case_viewer
        ).json()
        == []
    )
    assert (
        client.get(
            f"/cases/{case['id']}/timeline", headers=perm_case_viewer
        ).json()
        == []
    )
    detail = client.get(f"/cases/{case['id']}", headers=perm_case_viewer).json()
    assert detail["entities"] == [] and detail["timeline_events"] == []

    # After the owner runs the analysis, viewers can read the results.
    assert (
        client.post(f"/cases/{case['id']}/report", headers=perm_owner).status_code
        == 200
    )
    entities = client.get(
        f"/cases/{case['id']}/entities", headers=perm_case_viewer
    ).json()
    timeline = client.get(
        f"/cases/{case['id']}/timeline", headers=perm_case_viewer
    ).json()
    assert len(entities) > 0
    assert timeline == sorted(timeline, key=lambda e: e["sequence_order"])
    assert len(timeline) > 0
