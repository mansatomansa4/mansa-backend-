import pytest


@pytest.mark.django_db
def test_projects_list_sqlite_returns_503(client):
    resp = client.get("/api/platform/projects/")
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"]
