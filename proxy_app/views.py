import logging
import datetime
import httpx
from adrf.decorators import api_view

from django.http import HttpResponse

from rich.pretty import pretty_repr

from drf_proxy import settings

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST', 'DELETE'])
async def proxy_request(request, *args, **kwargs):
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

    await log_request(request, response, service_url)

    proxy_response = HttpResponse(
        content=response.content,
        status=response.status_code,
        content_type=response.headers.get('Content-type'),
    )

    for header, value in response.headers.items():
        if header.lower() not in ('content-type', 'content-length'):
            proxy_response[header] = value

    return proxy_response


async def log_request(request, response, service_url):
    log_data = {
        'time': datetime.datetime.now(),
        'user': str(request.user),
        'method': request.method,
        'path': request.get_full_path(),
        'headers': dict(request.headers),
        'files': request.FILES,
        'service_url': service_url,
        'response_status': response.status_code,
        'response_content': response.content,
    }
    logger.debug(pretty_repr(log_data))
