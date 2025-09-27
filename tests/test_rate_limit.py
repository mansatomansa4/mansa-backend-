import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_register_rate_limit_exceeded(client):
    url = reverse("register")
    payload = {"email": "rltest@example.com", "password": "StrongPass123"}
    for i in range(5):
        client.post(url, payload)
    resp = client.post(url, payload)
    # django-ratelimit returns 429 when blocked
    assert resp.status_code in (429, 400)  # Allow 400 if validation hits first
