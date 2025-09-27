import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_openapi_schema_available(client):
    url = reverse("schema")
    resp = client.get(url, HTTP_ACCEPT="application/json")
    assert resp.status_code == 200
    # drf-spectacular may return application/vnd.oai.openapi; charset=utf-8
    data = (
        resp.json()
        if "json" in resp.get("Content-Type")
        or resp.get("Content-Type", "").startswith("application/vnd.oai")
        else {}
    )
    assert data["info"]["title"] == "Mansa API"
    assert data["info"]["version"] == "0.1.0"
