import pytest
from django.urls import reverse

from apps.users.models import User


@pytest.mark.django_db
def test_token_obtain_and_me(client):
    User.objects.create_user(email="auth@example.com", password="StrongPass123")
    token_url = reverse("token_obtain_pair")
    resp = client.post(token_url, data={"email": "auth@example.com", "password": "StrongPass123"})
    assert resp.status_code == 200
    access = resp.json()["access"]

    me_url = reverse("me")
    me_resp = client.get(me_url, HTTP_AUTHORIZATION=f"Bearer {access}")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "auth@example.com"
