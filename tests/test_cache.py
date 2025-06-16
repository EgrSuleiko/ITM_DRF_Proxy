import pytest

from proxy_app.cache_utils import cache_by_path
from django.test import RequestFactory
from django.http import HttpResponse
from unittest.mock import patch


@pytest.fixture
def mock_view():
    async def view(request):
        return HttpResponse('original_content', status=200)

    return view


@pytest.mark.asyncio
async def test_cache_hit(mock_view):
    paths = ['/documents/file/123']
    decorated_view = cache_by_path(paths)(mock_view)

    factory = RequestFactory()
    request = factory.get('/documents/file/123')

    with patch('proxy_app.cache_utils.cache_server.cache') as mock_cache:
        mock_cache.get.return_value = {
            'content': b'cached_content',
            'status_code': 200,
            'content_type': 'text/plain'
        }

        response = await decorated_view(request)
        assert response.content == b'cached_content'
        mock_cache.get.assert_called_once()


@pytest.mark.asyncio
async def test_cache_miss(mock_view):
    paths = ['/documents/file/123']
    decorated_view = cache_by_path(paths)(mock_view)

    factory = RequestFactory()
    request = factory.get('/documents/file/123')

    with patch('proxy_app.cache_utils.cache_server.cache') as mock_cache:
        mock_cache.get.return_value = None

        response = await decorated_view(request)
        assert response.content == b'original_content'

        mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_non_get_request(mock_view):
    paths = ['/documents/file/123']
    decorated_view = cache_by_path(paths)(mock_view)

    factory = RequestFactory()
    request = factory.post('/documents/file/123')

    response = await decorated_view(request)
    assert response.content == b'original_content'
