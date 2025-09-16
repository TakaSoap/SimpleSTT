import base64

import pytest


@pytest.mark.asyncio
async def test_login_success(client, auth_headers):
    response = await client.post("/api/auth/login", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"


@pytest.mark.asyncio
async def test_login_failure(client):
    bad_token = base64.b64encode(b"tester:wrong").decode()
    response = await client.post(
        "/api/auth/login",
        headers={"Authorization": f"Basic {bad_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_validate_key_uses_default(client, auth_headers):
    response = await client.post(
        "/api/keys/validate",
        headers=auth_headers,
        json={"provider": {"provider": "openai"}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_default"] is True
    assert "default" in payload["message"].lower()
