# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

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
def admin_headers():
    return _login_as("admin-test", "adminpass123", is_admin=True)


@pytest.fixture
def alice_headers():
    return _login_as("alice-test", "alicepass123")


@pytest.fixture
def bob_headers():
    return _login_as("bob-test", "bobpass123")


def _create_case(headers: dict) -> dict:
    response = client.post(
        "/cases",
        json={
            "context": "Auditor reviewing possible vendor misuse",
            "description": "Invoices from a new vendor match employee bank details.",
            "evidence_items": [
                "2024-04-05: Invoice #1001 for $9,850.00 from Brightline Supply Co.",
                "Vendor account #55210984 matches employee payroll.",
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_unauthenticated_requests_rejected():
    assert client.get("/cases").status_code == 401
    assert client.post("/ai/assess-case", json={
        "context": "x", "description": "y", "evidence_items": []
    }).status_code == 401


def test_login_wrong_password_rejected(admin_headers):
    response = client.post(
        "/auth/login", data={"username": "admin-test", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_sets_httponly_session_cookie():
    init_db()
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, "cookie-test"):
            user_service.create_user(
                db, UserCreate(username="cookie-test", password="cookiepass123")
            )
    finally:
        db.close()

    response = client.post(
        "/auth/login", data={"username": "cookie-test", "password": "cookiepass123"}
    )
    assert response.status_code == 200
    cookie = response.cookies.get("access_token")
    assert cookie is not None
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header


def test_cookie_alone_authenticates_without_authorization_header():
    init_db()
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, "cookie-only-test"):
            user_service.create_user(
                db, UserCreate(username="cookie-only-test", password="cookiepass123")
            )
    finally:
        db.close()

    with TestClient(app) as session_client:
        login_response = session_client.post(
            "/auth/login",
            data={"username": "cookie-only-test", "password": "cookiepass123"},
        )
        assert login_response.status_code == 200
        # No Authorization header -- only the cookie the client jar now
        # holds from the login response.
        me_response = session_client.get("/auth/me")
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "cookie-only-test"


def test_logout_revokes_token_immediately(alice_headers):
    assert client.get("/auth/me", headers=alice_headers).status_code == 200

    logout_response = client.post("/auth/logout", headers=alice_headers)
    assert logout_response.status_code == 204

    # The same bearer token must now be rejected even though it hasn't
    # naturally expired -- this is the point of server-side revocation.
    assert client.get("/auth/me", headers=alice_headers).status_code == 401


def test_logout_clears_session_cookie():
    init_db()
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, "logout-cookie-test"):
            user_service.create_user(
                db,
                UserCreate(username="logout-cookie-test", password="cookiepass123"),
            )
    finally:
        db.close()

    with TestClient(app) as session_client:
        session_client.post(
            "/auth/login",
            data={"username": "logout-cookie-test", "password": "cookiepass123"},
        )
        assert session_client.get("/auth/me").status_code == 200

        logout_response = session_client.post("/auth/logout")
        assert logout_response.status_code == 204

        assert session_client.get("/auth/me").status_code == 401


def test_non_admin_cannot_create_users(alice_headers):
    response = client.post(
        "/auth/users",
        json={"username": "sneaky", "password": "sneakypass1"},
        headers=alice_headers,
    )
    assert response.status_code == 403


def test_user_creation_validates_input(admin_headers):
    response = client.post(
        "/auth/users",
        json={"username": "ab", "password": "short"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_case_invisible_to_non_collaborator(admin_headers, alice_headers):
    case = _create_case(admin_headers)

    assert (
        client.get(f"/cases/{case['id']}", headers=alice_headers).status_code == 404
    )
    listed_ids = [c["id"] for c in client.get("/cases", headers=alice_headers).json()]
    assert case["id"] not in listed_ids


def test_sharing_grants_view_and_edit(admin_headers, alice_headers):
    case = _create_case(admin_headers)

    response = client.post(
        f"/cases/{case['id']}/collaborators",
        json={"username": "alice-test", "role": "editor"},
        headers=admin_headers,
    )
    assert response.status_code == 200

    assert (
        client.get(f"/cases/{case['id']}", headers=alice_headers).status_code == 200
    )
    listed_ids = [c["id"] for c in client.get("/cases", headers=alice_headers).json()]
    assert case["id"] in listed_ids

    response = client.post(
        f"/cases/{case['id']}/evidence",
        json={"title": "note", "type": "", "content": "added by collaborator"},
        headers=alice_headers,
    )
    assert response.status_code == 200


def test_collaborator_cannot_manage_collaborators(
    admin_headers, alice_headers, bob_headers
):
    case = _create_case(admin_headers)
    client.post(
        f"/cases/{case['id']}/collaborators",
        json={"username": "alice-test", "role": "editor"},
        headers=admin_headers,
    )

    response = client.post(
        f"/cases/{case['id']}/collaborators",
        json={"username": "bob-test", "role": "viewer"},
        headers=alice_headers,
    )
    assert response.status_code == 403


def test_case_deletion_rules(admin_headers, alice_headers, bob_headers):
    case = _create_case(admin_headers)
    client.post(
        f"/cases/{case['id']}/collaborators",
        json={"username": "alice-test", "role": "editor"},
        headers=admin_headers,
    )

    # A stranger can't even see it -- delete looks like a missing case.
    assert (
        client.delete(f"/cases/{case['id']}", headers=bob_headers).status_code == 404
    )
    # A collaborator can see it but may not delete it.
    assert (
        client.delete(f"/cases/{case['id']}", headers=alice_headers).status_code == 403
    )
    # The owner can delete it.
    assert (
        client.delete(f"/cases/{case['id']}", headers=admin_headers).status_code == 204
    )
    assert (
        client.get(f"/cases/{case['id']}", headers=admin_headers).status_code == 404
    )


def test_full_pipeline_mock(admin_headers):
    case = _create_case(admin_headers)

    response = client.post(f"/cases/{case['id']}/report", headers=admin_headers)
    assert response.status_code == 200
    sections = response.json()["sections"]
    assert set(sections) == {
        "overview",
        "evidence",
        "entities",
        "timeline",
        "risk_assessment",
        "recommendations",
    }

    detail = client.get(f"/cases/{case['id']}", headers=admin_headers).json()
    assert len(detail["entities"]) > 0
    assert len(detail["timeline_events"]) > 0
    assert len(detail["risk_assessments"]) == 1
    assert len(detail["reports"]) == 1
    assert detail["owner"]["username"] == "admin-test"


def test_username_change_does_not_invalidate_existing_token(alice_headers):
    # The token was issued before the rename -- it must keep working, since
    # it identifies the user by permanent id, not by username.
    response = client.put(
        "/auth/me",
        json={"username": "alice-renamed", "display_name": None, "avatar_url": None},
        headers=alice_headers,
    )
    assert response.status_code == 200
    assert response.json()["username"] == "alice-renamed"

    me = client.get("/auth/me", headers=alice_headers)
    assert me.status_code == 200
    assert me.json()["username"] == "alice-renamed"

    # Rename back so other tests using "alice-test" aren't affected.
    client.put(
        "/auth/me",
        json={"username": "alice-test", "display_name": None, "avatar_url": None},
        headers=alice_headers,
    )


def test_username_change_rejects_collision(admin_headers, alice_headers):
    response = client.put(
        "/auth/me",
        json={"username": "admin-test", "display_name": None, "avatar_url": None},
        headers=alice_headers,
    )
    assert response.status_code == 400


def test_avatar_url_requires_http_scheme(alice_headers):
    response = client.put(
        "/auth/me",
        json={
            "username": None,
            "display_name": None,
            "avatar_url": "javascript:alert(1)",
        },
        headers=alice_headers,
    )
    assert response.status_code == 400


def test_user_list_hides_permission_metadata(admin_headers, alice_headers):
    # The all-users listing (collaborator picker) must not expose roles.
    summary = client.get("/auth/users", headers=alice_headers).json()
    assert len(summary) > 0
    assert all("global_role" not in u and "is_admin" not in u for u in summary)

    # The detailed listing includes them but is admin-only.
    assert (
        client.get("/auth/users/detailed", headers=alice_headers).status_code == 403
    )
    detailed = client.get("/auth/users/detailed", headers=admin_headers).json()
    assert all("global_role" in u and "is_admin" in u for u in detailed)


def test_avatar_color_rejects_arbitrary_value(alice_headers):
    response = client.put(
        "/auth/me",
        json={
            "username": None,
            "display_name": None,
            "avatar_url": None,
            "avatar_color": "#ffffff",
        },
        headers=alice_headers,
    )
    assert response.status_code == 400


def test_login_locks_out_account_after_repeated_failures(admin_headers):
    # Dedicated username so this test's lockout can't bleed into other
    # tests that reuse "admin-test"/"alice-test"/"bob-test".
    username = "ratelimit-test"
    password = "ratelimitpass1"
    db = SessionLocal()
    try:
        if not user_service.get_user_by_username(db, username):
            user_service.create_user(
                db, UserCreate(username=username, password=password)
            )
    finally:
        db.close()

    for _ in range(settings.LOGIN_RATE_LIMIT_ATTEMPTS):
        response = client.post(
            "/auth/login", data={"username": username, "password": "wrong"}
        )
        assert response.status_code == 401

    # The account is now locked out -- even the *correct* password is
    # rejected until the lockout window passes.
    response = client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    assert response.status_code == 429
    assert "Retry-After" in response.headers

    # A different, unrelated account from the same test client is not
    # affected by another account's lockout.
    response = client.post(
        "/auth/login", data={"username": "admin-test", "password": "adminpass123"}
    )
    assert response.status_code == 200


def test_avatar_color_accepts_allowed_palette_value(alice_headers):
    response = client.put(
        "/auth/me",
        json={
            "username": None,
            "display_name": None,
            "avatar_url": None,
            "avatar_color": "#9333ea",
        },
        headers=alice_headers,
    )
    assert response.status_code == 200
    assert response.json()["avatar_color"] == "#9333ea"

    me = client.get("/auth/me", headers=alice_headers)
    assert me.json()["avatar_color"] == "#9333ea"
