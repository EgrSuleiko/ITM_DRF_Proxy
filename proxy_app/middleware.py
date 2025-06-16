import logging
import time

from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


class LoggingRequestMiddleware:
    """Класс для логирования поступающих запросов"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timestamp = time.monotonic()
        response = self.get_response(request)
        self.log_request(request, response, time.monotonic() - timestamp)
        return response

    def log_request(self, request, response, timedelta):
        """Передает в логгер информацию запроса и ответа, а также время выполнения запроса"""
        log_data = {
            'request': {
                'user': str(request.user),
                'ip': self.get_client_ip(request),
                'method': request.method,
                'path': request.get_full_path(),
                'headers': dict(request.headers),
                'files': request.FILES,
            },
            'response': {
                'response_status': response.status_code,
                'response_content_type': response.headers.get('Content-Type', ''),
            },
            'performance_duration': f'{timedelta:.3f} seconds',

        }
        logger.debug(pretty_repr(log_data))

    @staticmethod
    def get_client_ip(request):
        """Получаем реальный IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
