# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

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
def es_owner():
    return _login_as("es-owner", "esownerpass1")


@pytest.fixture
def es_viewer():
    return _login_as("es-viewer", "esviewerpass1")


@pytest.fixture
def es_stranger():
    return _login_as("es-stranger", "esstrangerpass1")


def _create_case(headers: dict) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": "Entity search test case",
            "description": "Exercises the entity search tool.",
            "evidence_items": [],
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


def test_standalone_search_is_persisted_and_scoped_to_creator(es_owner, es_stranger):
    response = client.post(
        "/tools/entity-search",
        json={"query": "Acme Corp", "entity_type": "company"},
        headers=es_owner,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Acme Corp"
    assert body["provider"] == "mock"
    assert body["case_id"] is None
    assert body["summary"]
    assert body["sources"]

    mine = client.get("/tools/entity-search", headers=es_owner).json()
    assert any(s["id"] == body["id"] for s in mine)

    others = client.get("/tools/entity-search", headers=es_stranger).json()
    assert all(s["id"] != body["id"] for s in others)


def test_case_linked_search_requires_edit_access(es_owner, es_viewer, es_stranger):
    case = _create_case(es_owner)
    _add_collaborator(es_owner, case["id"], es_viewer, "viewer")

    # Viewer can't create a case-linked search (needs edit access).
    assert (
        client.post(
            "/tools/entity-search",
            json={"query": "Jane Doe", "case_id": case["id"]},
            headers=es_viewer,
        ).status_code
        == 403
    )

    # A stranger with no access gets a 404, not a 403 (case existence isn't leaked).
    assert (
        client.post(
            "/tools/entity-search",
            json={"query": "Jane Doe", "case_id": case["id"]},
            headers=es_stranger,
        ).status_code
        == 404
    )

    response = client.post(
        "/tools/entity-search",
        json={"query": "Jane Doe", "case_id": case["id"]},
        headers=es_owner,
    )
    assert response.status_code == 200
    assert response.json()["case_id"] == case["id"]

    # The viewer can still see it in the case's list (view access is enough to read).
    case_searches = client.get(
        f"/tools/entity-search?case_id={case['id']}", headers=es_viewer
    ).json()
    assert len(case_searches) == 1

    assert (
        client.get(
            f"/tools/entity-search?case_id={case['id']}", headers=es_stranger
        ).status_code
        == 404
    )


def test_get_single_search_respects_access(es_owner, es_stranger):
    response = client.post(
        "/tools/entity-search", json={"query": "Solo Search"}, headers=es_owner
    )
    search_id = response.json()["id"]

    assert (
        client.get(f"/tools/entity-search/{search_id}", headers=es_owner).status_code
        == 200
    )
    assert (
        client.get(
            f"/tools/entity-search/{search_id}", headers=es_stranger
        ).status_code
        == 404
    )
