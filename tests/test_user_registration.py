import pytest
from django.urls import reverse

from apps.users.models import User


@pytest.mark.django_db
def test_user_registration(client):
    url = reverse("register")
    payload = {
        "email": "test@example.com",
        "password": "StrongPass123",
        "first_name": "Test",
        "last_name": "User",
    }
    response = client.post(url, data=payload)
    assert response.status_code == 201
    assert User.objects.filter(email="test@example.com").exists()
