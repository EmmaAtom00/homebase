import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_health_says_ok():
    response = APIClient().get(reverse('health_check'))
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
