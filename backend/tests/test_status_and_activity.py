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


@pytest.fixture
def sa_owner():
    return _login_as("sa-owner", "saownerpass1")


@pytest.fixture
def sa_manager():
    return _login_as("sa-manager", "samanagerpass1")


@pytest.fixture
def sa_editor():
    return _login_as("sa-editor", "saeditorpass1")


@pytest.fixture
def sa_viewer():
    return _login_as("sa-viewer", "saviewerpass1")


@pytest.fixture
def sa_stranger():
    return _login_as("sa-stranger", "sastrangerpass1")


def _create_case(headers: dict) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": "Status and activity test case",
            "description": "Exercises the case lifecycle and audit trail.",
            "evidence_items": [
                "2024-04-05: Invoice #1001 for $9,850.00 from Brightline Supply Co."
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _add_collaborator(owner_headers, case_id, target_headers, role):
    username = client.get("/auth/me", headers=target_headers).json()["username"]
    response = client.post(
        f"/cases/{case_id}/collaborators",
        json={"username": username, "role": role},
        headers=owner_headers,
    )
    assert response.status_code == 200


def _set_status(headers, case_id, status):
    return client.patch(
        f"/cases/{case_id}/status", json={"status": status}, headers=headers
    )


def test_new_case_defaults_to_open(sa_owner):
    case = _create_case(sa_owner)
    assert case["status"] == "open"
    listed = client.get("/cases", headers=sa_owner).json()
    assert all("status" in c for c in listed)


def test_status_change_rights(sa_owner, sa_manager, sa_editor, sa_viewer):
    case = _create_case(sa_owner)
    _add_collaborator(sa_owner, case["id"], sa_manager, "manager")
    _add_collaborator(sa_owner, case["id"], sa_editor, "editor")
    _add_collaborator(sa_owner, case["id"], sa_viewer, "viewer")

    assert _set_status(sa_viewer, case["id"], "in_review").status_code == 403
    assert _set_status(sa_editor, case["id"], "in_review").status_code == 403

    response = _set_status(sa_manager, case["id"], "in_review")
    assert response.status_code == 200
    assert response.json()["status"] == "in_review"

    response = _set_status(sa_owner, case["id"], "closed")
    assert response.status_code == 200
    assert response.json()["status"] == "closed"

    assert _set_status(sa_owner, case["id"], "archived").status_code == 400


def test_closed_case_locks_edits_until_reopened(sa_owner):
    case = _create_case(sa_owner)
    assert _set_status(sa_owner, case["id"], "closed").status_code == 200

    # Even the owner can't add evidence or run analysis on a closed case.
    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "late", "type": "", "content": "should be blocked"},
            headers=sa_owner,
        ).status_code
        == 409
    )
    assert (
        client.post(f"/cases/{case['id']}/report", headers=sa_owner).status_code
        == 409
    )
    assert (
        client.post(
            f"/cases/{case['id']}/risk-assessment", headers=sa_owner
        ).status_code
        == 409
    )

    # Reopening restores both.
    assert _set_status(sa_owner, case["id"], "open").status_code == 200
    assert (
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": "late", "type": "", "content": "allowed again"},
            headers=sa_owner,
        ).status_code
        == 200
    )
    assert (
        client.post(f"/cases/{case['id']}/report", headers=sa_owner).status_code
        == 200
    )


def test_collaborator_management_allowed_on_closed_case(
    sa_owner, sa_manager, sa_viewer
):
    case = _create_case(sa_owner)
    assert _set_status(sa_owner, case["id"], "closed").status_code == 200

    _add_collaborator(sa_owner, case["id"], sa_manager, "manager")
    _add_collaborator(sa_owner, case["id"], sa_viewer, "viewer")
    viewer_id = client.get("/auth/me", headers=sa_viewer).json()["id"]
    assert (
        client.delete(
            f"/cases/{case['id']}/collaborators/{viewer_id}", headers=sa_owner
        ).status_code
        == 204
    )


def test_activity_log_records_and_orders_events(sa_owner, sa_viewer, sa_stranger):
    case = _create_case(sa_owner)
    _add_collaborator(sa_owner, case["id"], sa_viewer, "viewer")

    client.post(
        f"/cases/{case['id']}/evidence",
        json={"title": "Bank statement", "type": "", "content": "acct details"},
        headers=sa_owner,
    )
    client.post(f"/cases/{case['id']}/report", headers=sa_owner)
    _set_status(sa_owner, case["id"], "in_review")

    # A per-case viewer can read the log; a stranger can't see the case.
    assert (
        client.get(f"/cases/{case['id']}/activity", headers=sa_stranger).status_code
        == 404
    )
    entries = client.get(
        f"/cases/{case['id']}/activity", headers=sa_viewer
    ).json()

    actions = [e["action"] for e in entries]
    # Newest first.
    assert actions == [
        "status_changed",
        "analysis_run",
        "evidence_added",
        "collaborator_added",
        "case_created",
    ]
    assert all(e["actor"]["username"] == "sa-owner" for e in entries)
    assert entries[0]["detail"] == "changed status from Open to In Review"
    assert entries[2]["detail"] == 'added evidence "Bank statement"'