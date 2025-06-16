import httpx
from adrf.decorators import api_view
from django.http import HttpResponse
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from drf_proxy import settings
from proxy_app.cache_utils import cache_by_path


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@cache_by_path([r'/documents/file/', r'/documents/get_text/'])
async def proxy_request(request, *args, **kwargs):
    """
    Пробрасывает входящий запрос к сервису, указанному в настройках
    """
    service_url = f'{settings.FASTAPI_URL}{request.get_full_path()}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=service_url,
                files=request.FILES,
            )
        except httpx.RequestError as e:
            return HttpResponse(str(e), status=503)

    proxy_response = HttpResponse(
        content=response.content,
        status=response.status_code,
        content_type=response.headers.get('Content-type'),
    )

    return proxy_response
