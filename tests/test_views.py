from unittest.mock import AsyncMock, patch

import httpx
import pytest
from django.test import RequestFactory
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient
from proxy_app.views import proxy_request


@pytest.fixture
def response_fixture():
    mock_response = AsyncMock()
    mock_response.content = b'content'
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/plain'}
    return mock_response


@pytest.fixture
def factory_fixture():
    return RequestFactory()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_proxy_request_failure(factory_fixture):
    user = User.objects.create_user(username='test1', password='test')

    access_token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')

    request = factory_fixture.get('/any/proxy/path', HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')
    request.user = user

    with patch('httpx.AsyncClient.request', side_effect=httpx.RequestError('Unavailable')):
        response = await proxy_request(request)
        assert response.status_code == 503
        assert response.content == b'Unavailable'


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_proxy_success(factory_fixture, response_fixture):
    user = User.objects.create_user(username='test2', password='test')

    access_token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')

    request = factory_fixture.get('/any/proxy/path', HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')
    request.user = user

    with patch('httpx.AsyncClient.request', return_value=response_fixture):
        response = await proxy_request(request)
        assert response.status_code == 200
        assert response.content == b'content'


@pytest.mark.asyncio
async def test_authentication_failure(factory_fixture):
    request = factory_fixture.get('/any/proxy/path')

    response = await proxy_request(request)
    assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_authentication_success(factory_fixture, response_fixture):
    user = User.objects.create_user(username='test3', password='test')

    access_token = AccessToken.for_user(user)

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')

    request = factory_fixture.get('/any/proxy/path', HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')
    request.user = user

    with patch('httpx.AsyncClient.request', return_value=response_fixture):
        response = await proxy_request(request)
        assert response.status_code == 200
        assert response.content == b'content'
