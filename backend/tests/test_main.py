# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Spyridon Drakopoulos

import pytest
from fastapi.testclient import TestClient

from app.database.db import SessionLocal, init_db
from app.main import app
from app.schemas.user_schema import UserCreate
from app.services import user_service

client = TestClient(app)


@pytest.fixture
def auth_headers():
    init_db()
    db = SessionLocal()
    try:
        username = "test-user"
        password = "testpass123"
        if not user_service.get_user_by_username(db, username):
            user_service.create_user(
                db, UserCreate(username=username, password=password)
            )
    finally:
        db.close()

    response = client.post(
        "/auth/login", data={"username": username, "password": password}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Fraud Investigation Workbench API is running"


def test_health_reports_ok_when_db_is_reachable():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_assess_case(auth_headers):
    response = client.post(
        "/ai/assess-case",
        json={
            "context": "Auditor reviewing possible vendor misuse",
            "description": "Several invoices were submitted by a new vendor.",
            "evidence_items": ["invoice 1001", "vendor bank account"]
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["low", "medium"]
    assert "risk_indicators" in data
    assert "next_steps" in data
    assert "draft_summary" in data
