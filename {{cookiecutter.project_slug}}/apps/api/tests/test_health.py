from http import HTTPStatus

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_endpoint(client):
    """
    Test if the health check endpoint is accessible and returns the correct response
    """
    url = reverse("api:v1:health-check")
    
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    
    response_data = response.json()
    assert response_data["code"] == 0
    assert response_data["message"] == "success"
    assert response_data["data"]["status"] == "ok"
    assert response_data["data"]["message"] == "API is running"
