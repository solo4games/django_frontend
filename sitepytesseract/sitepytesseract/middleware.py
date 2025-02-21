from prometheus_client import Counter, Histogram
import time

request_total = Counter('request_total',
                        'Total number of requests',
                        ['method',
                         'full_path',
                         'ip',
                         'user_agent',
                         'referrer',
                         'http_host',
                         'server_name'])

request_time = Histogram('request_processing_seconds',
                       'Time spent processing requests',
                       ['method', 'full_path', 'ip', 'http_host', 'server_name'],
                         buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0])


class StatisticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        method = request.method
        full_path = request.get_full_path()
        ip = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        http_host = request.META.get('HTTP_HOST', '')
        server_name = request.META.get('SERVER_NAME', '')

        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        request_total.labels(method, full_path, ip, user_agent, referrer, http_host, server_name).inc()
        request_time.labels(method, full_path, ip, http_host, server_name).observe(duration)

        return response
