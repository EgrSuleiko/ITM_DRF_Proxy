import re
import time
from typing import Callable

import redis.exceptions
from django.core.cache import caches
from django.http import HttpResponse

from drf_proxy import settings

cache = caches['default']


def cache_by_path(paths: list[str]) -> Callable:
    """Декоратор для кэширования GET-запросов по адресам paths"""

    def cache_decorator(view_func: Callable) -> Callable:

        async def wrapper(request, *args, **kwargs):
            full_path = request.get_full_path()

            if time.time() - settings.REDIS_HEALTH_LAST_CHECK >= settings.REDIS_HEALTH_CHECK_INTERVAL:
                print('check redis health')
                await redis_check_health()
                settings.REDIS_HEALTH_LAST_CHECK = time.time()

            if (settings.REDIS_HEALTH and
                    request.method == 'GET' and
                    any(map(lambda x: re.compile(x).search(full_path), paths))):
                cached_key = f'doc_cache:{full_path}'

                try:
                    cached_response = cache.get(cached_key)
                except redis.exceptions.ConnectionError:
                    settings.REDIS_HEALTH = False
                    return await view_func(request, *args, **kwargs)

                if cached_response:
                    return HttpResponse(
                        content=cached_response['content'],
                        status=cached_response['status_code'],
                        content_type=cached_response['content_type'],
                    )

                response = await view_func(request, *args, **kwargs)

                if response.status_code == 200:
                    cached_data = {
                        'content': response.content,
                        'status_code': response.status_code,
                        'content_type': response.headers.get('Content-type'),
                    }
                    cache.set(cached_key, cached_data, timeout=settings.CACHE_TTL)

                return response

            return await view_func(request, *args, **kwargs)

        return wrapper

    return cache_decorator


async def redis_check_health():
    """
    Проверяет работоспособность Redis.
    В случае, если сервис не отвечает на пинг запрос, меняет глобальную переменную в настройках на False
    """
    try:
        if cache.client.get_client().ping():
            settings.REDIS_HEALTH = True
            print('redis health TRUE')
        else:
            settings.REDIS_HEALTH = False
            print('redis health FALSE')
    except redis.exceptions.ConnectionError:
        settings.REDIS_HEALTH = False
        print('redis health FALSE')
