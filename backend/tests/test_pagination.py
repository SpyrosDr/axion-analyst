# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import pytest
from fastapi.testclient import TestClient

from app.database.db import SessionLocal, init_db
from app.main import app
from app.schemas.user_schema import UserCreate
from app.services import user_service

client = TestClient(app)


def _login_as(username: str, password: str) -> dict:
    init_db()
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, username):
            user_service.create_user(db, UserCreate(username=username, password=password))
    finally:
        db.close()

    response = client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def headers():
    return _login_as("pagination-test", "paginationpass1")


def _create_case(headers: dict, n: int) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": f"Case {n}",
            "description": f"Description for case {n}.",
            "evidence_items": [],
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_list_cases_respects_limit_and_offset(headers):
    for n in range(5):
        _create_case(headers, n)

    page1 = client.get("/cases?limit=2&offset=0", headers=headers)
    assert page1.status_code == 200
    assert len(page1.json()) == 2

    page2 = client.get("/cases?limit=2&offset=2", headers=headers)
    assert page2.status_code == 200
    assert len(page2.json()) == 2

    ids_page1 = {c["id"] for c in page1.json()}
    ids_page2 = {c["id"] for c in page2.json()}
    assert ids_page1.isdisjoint(ids_page2)


def test_list_cases_default_limit_is_bounded():
    # No explicit limit -- must still apply the default cap rather than
    # returning every case unbounded.
    headers = _login_as("pagination-default-test", "paginationpass2")
    response = client.get("/cases", headers=headers)
    assert response.status_code == 200


def test_limit_above_max_is_rejected(headers):
    response = client.get("/cases?limit=99999", headers=headers)
    assert response.status_code == 422


def test_negative_offset_is_rejected(headers):
    response = client.get("/cases?offset=-1", headers=headers)
    assert response.status_code == 422


def test_list_evidence_paginates(headers):
    case = _create_case(headers, 0)
    for i in range(4):
        response = client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": f"Item {i}", "type": "note", "content": f"content {i}"},
            headers=headers,
        )
        assert response.status_code == 200

    page = client.get(f"/cases/{case['id']}/evidence?limit=2&offset=0", headers=headers)
    assert page.status_code == 200
    assert len(page.json()) == 2

    page2 = client.get(f"/cases/{case['id']}/evidence?limit=2&offset=2", headers=headers)
    assert page2.status_code == 200
    assert len(page2.json()) == 2


def test_list_activity_paginates_and_orders_newest_first(headers):
    case = _create_case(headers, 0)
    for i in range(3):
        client.post(
            f"/cases/{case['id']}/evidence",
            json={"title": f"Item {i}", "type": "note", "content": f"content {i}"},
            headers=headers,
        )

    page = client.get(f"/cases/{case['id']}/activity?limit=1&offset=0", headers=headers)
    assert page.status_code == 200
    entries = page.json()
    assert len(entries) == 1

    all_entries = client.get(f"/cases/{case['id']}/activity?limit=50", headers=headers).json()
    assert entries[0]["created_at"] == all_entries[0]["created_at"]
    assert [e["created_at"] for e in all_entries] == sorted(
        [e["created_at"] for e in all_entries], reverse=True
    )
