import pytest
from django.db import connection
from django.urls import reverse


@pytest.mark.django_db
def test_project_filtering_503_on_sqlite(client):
    # On sqlite fallback we should still see 503 for listing (guarded)
    assert "sqlite" in connection.vendor
    resp = client.get(
        reverse("project-list"),
        {"status": "open"},
    )
    assert resp.status_code == 503


# NOTE: A real filtering test would require Postgres + data fixtures.
# Skipped in sqlite mode.
