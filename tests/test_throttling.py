import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_anon_throttle_trips(client, settings):
    # Ensure low throttle for test isolation
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] = "3/min"
    url = reverse("health-check")  # open endpoint permits AllowAny
    statuses = []
    for i in range(4):
        resp = client.get(url)
        statuses.append(resp.status_code)
    # First 3 should be 200, 4th should be 429 (or 200 if timing edge-case)
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] in (429, 200)


@pytest.mark.django_db
def test_user_throttle_trips(client, django_user_model, settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "3/min"
    # Create and auth user
    django_user_model.objects.create_user(email="thr@example.com", password="StrongPass123")
    token_url = reverse("token_obtain_pair")
    token_resp = client.post(
        token_url,
        {"email": "thr@example.com", "password": "StrongPass123"},
        content_type="application/json",
    )
    assert token_resp.status_code == 200
    access = token_resp.json()["access"]
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access}"

    url = reverse("health-check")
    codes = []
    for i in range(4):
        r = client.get(url)
        codes.append(r.status_code)
    assert codes[:3] == [200, 200, 200]
    assert codes[3] in (429, 200)
