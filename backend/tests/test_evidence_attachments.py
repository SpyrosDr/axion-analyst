# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import pytest
from fastapi.testclient import TestClient

from app.config import settings
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
def ea_owner():
    return _login_as("ea-owner", "eaownerpass1")


@pytest.fixture
def ea_viewer():
    return _login_as("ea-viewer", "eaviewerpass1")


@pytest.fixture
def ea_stranger():
    return _login_as("ea-stranger", "eastrangerpass1")


def _create_case(headers: dict) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": "Evidence attachment test case",
            "description": "Exercises the attachments endpoints.",
            "evidence_items": ["Initial evidence item."],
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


def _evidence_id(case: dict, headers: dict) -> int:
    # POST /cases only returns CaseResponse (no evidence_items) --
    # GET .../{id} returns the full CaseDetailResponse that has them.
    detail = client.get(f"/cases/{case['id']}", headers=headers)
    assert detail.status_code == 200
    return detail.json()["evidence_items"][0]["id"]


def _attachments_url(case_id: int, evidence_id: int) -> str:
    return f"/cases/{case_id}/evidence/{evidence_id}/attachments"


def test_upload_list_and_download_roundtrip(ea_owner):
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)

    upload = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("screenshot.png", b"fake-png-bytes", "image/png")},
        headers=ea_owner,
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["filename"] == "screenshot.png"
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(b"fake-png-bytes")
    assert body["evidence_id"] == evidence_id
    assert "storage_key" not in body  # internal, never exposed to clients

    listing = client.get(_attachments_url(case["id"], evidence_id), headers=ea_owner)
    assert listing.status_code == 200
    assert [a["id"] for a in listing.json()] == [body["id"]]

    download = client.get(
        f"{_attachments_url(case['id'], evidence_id)}/{body['id']}/download",
        headers=ea_owner,
    )
    assert download.status_code == 200
    assert download.content == b"fake-png-bytes"
    assert "attachment" in download.headers["content-disposition"]
    assert "screenshot.png" in download.headers["content-disposition"]


def test_disallowed_extension_is_rejected(ea_owner):
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)

    response = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
        headers=ea_owner,
    )
    assert response.status_code == 400

    assert client.get(
        _attachments_url(case["id"], evidence_id), headers=ea_owner
    ).json() == []


def test_oversized_upload_is_rejected(ea_owner, monkeypatch):
    monkeypatch.setattr(settings, "EVIDENCE_MAX_ATTACHMENT_SIZE_BYTES", 10)
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)

    response = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("big.txt", b"x" * 100, "text/plain")},
        headers=ea_owner,
    )
    assert response.status_code == 413

    assert client.get(
        _attachments_url(case["id"], evidence_id), headers=ea_owner
    ).json() == []


def test_viewer_cannot_upload_or_delete_but_can_view(
    ea_owner, ea_viewer, ea_stranger
):
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)
    _add_collaborator(ea_owner, case["id"], ea_viewer, "viewer")

    upload = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=ea_owner,
    )
    attachment_id = upload.json()["id"]

    # Viewer (case access, no edit) can list/download but not upload/delete.
    assert (
        client.get(
            _attachments_url(case["id"], evidence_id), headers=ea_viewer
        ).status_code
        == 200
    )
    assert (
        client.post(
            _attachments_url(case["id"], evidence_id),
            files={"file": ("x.txt", b"x", "text/plain")},
            headers=ea_viewer,
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"{_attachments_url(case['id'], evidence_id)}/{attachment_id}",
            headers=ea_viewer,
        ).status_code
        == 403
    )

    # A stranger with no case access at all gets 404, not 403 (case
    # existence isn't leaked), for every one of these routes.
    assert (
        client.get(
            _attachments_url(case["id"], evidence_id), headers=ea_stranger
        ).status_code
        == 404
    )
    assert (
        client.post(
            _attachments_url(case["id"], evidence_id),
            files={"file": ("x.txt", b"x", "text/plain")},
            headers=ea_stranger,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{_attachments_url(case['id'], evidence_id)}/{attachment_id}/download",
            headers=ea_stranger,
        ).status_code
        == 404
    )


def test_evidence_id_is_scoped_to_the_case_in_the_url(ea_owner):
    case_a = _create_case(ea_owner)
    case_b = _create_case(ea_owner)
    evidence_a = _evidence_id(case_a, ea_owner)
    evidence_b = _evidence_id(case_b, ea_owner)

    # evidence_a genuinely belongs to case_a, not case_b -- asking for it
    # through case_b's URL must 404, not silently resolve cross-case.
    response = client.get(
        _attachments_url(case_b["id"], evidence_a), headers=ea_owner
    )
    assert response.status_code == 404
    assert evidence_b != evidence_a


def test_delete_removes_attachment_and_download_then_404s(ea_owner):
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)

    upload = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=ea_owner,
    )
    attachment_id = upload.json()["id"]

    delete = client.delete(
        f"{_attachments_url(case['id'], evidence_id)}/{attachment_id}",
        headers=ea_owner,
    )
    assert delete.status_code == 204

    assert (
        client.get(
            f"{_attachments_url(case['id'], evidence_id)}/{attachment_id}/download",
            headers=ea_owner,
        ).status_code
        == 404
    )
    assert (
        client.get(_attachments_url(case["id"], evidence_id), headers=ea_owner).json()
        == []
    )


def test_upload_and_delete_blocked_on_closed_case(ea_owner):
    case = _create_case(ea_owner)
    evidence_id = _evidence_id(case, ea_owner)

    upload = client.post(
        _attachments_url(case["id"], evidence_id),
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=ea_owner,
    )
    attachment_id = upload.json()["id"]

    close = client.patch(
        f"/cases/{case['id']}/status", json={"status": "closed"}, headers=ea_owner
    )
    assert close.status_code == 200

    assert (
        client.post(
            _attachments_url(case["id"], evidence_id),
            files={"file": ("x.txt", b"x", "text/plain")},
            headers=ea_owner,
        ).status_code
        == 409
    )
    assert (
        client.delete(
            f"{_attachments_url(case['id'], evidence_id)}/{attachment_id}",
            headers=ea_owner,
        ).status_code
        == 409
    )
