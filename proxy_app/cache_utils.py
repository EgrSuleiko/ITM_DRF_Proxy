import logging
import re
import time
from typing import Callable

import redis.exceptions
from django.core.cache import caches
from django.http import HttpResponse

from drf_proxy import settings

logger = logging.getLogger(__name__)


class CacheRedis:
    """Класс для взаимодействия с библиотекой django.core.cache"""

    def __init__(self, cache_name: str = 'default'):
        self.cache = caches[cache_name]
        self.health = False
        self.last_check = 0

    async def check_health(self):
        """
        Проверяет работоспособность Redis.
        В случае, если сервис не отвечает на пинг запрос, меняет глобальную переменную в настройках на False
        """
        try:
            if self.cache.client.get_client().ping():
                self.health = True
                logger.info('Redis health is OK')
                return True
        except BaseException:
            pass
        self.health = False
        logger.info('Redis is NOT working')
        return False


cache_server = CacheRedis('default')


def cache_by_path(paths: list[str]) -> Callable:
    """Декоратор для кэширования GET-запросов по адресам paths"""

    def cache_decorator(view_func: Callable) -> Callable:

        async def wrapper(request, *args, **kwargs):
            full_path = request.get_full_path()

            if time.time() - cache_server.last_check >= settings.REDIS_HEALTH_CHECK_INTERVAL:
                await cache_server.check_health()
                cache_server.last_check = time.time()

            if (
                    cache_server.health and
                    request.method == 'GET' and
                    any(map(lambda x: re.compile(x).search(full_path), paths))
            ):
                cached_key = f'doc_cache:{full_path}'

                try:
                    cached_response = cache_server.cache.get(cached_key)
                except redis.exceptions.ConnectionError:
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
                    cache_server.cache.set(cached_key, cached_data, timeout=settings.CACHE_TTL)

                return response

            return await view_func(request, *args, **kwargs)

        return wrapper

    return cache_decorator
