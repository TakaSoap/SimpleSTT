import pytest


@pytest.mark.asyncio
async def test_options_returns_defaults(client, auth_headers):
    response = await client.get("/api/options", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()

    defaults = payload["defaults"]
    assert defaults["provider"] == "azure"
    assert defaults["model"] == "gpt-4o-mini-transcribe"
    assert defaults["language"] == "en"
    assert defaults["stream_enabled"] is False
    assert defaults["azure_endpoint"] == "https://example.openai.azure.com/"
    assert defaults["azure_deployment_id"] == "test-deploy"
    assert defaults["azure_api_version"] == "2024-01-01-preview"

    assert payload["languages"]
    assert payload["models"]
    assert payload["has_default_keys"]["openai"] is True
    assert payload["has_default_keys"]["azure"] is True
