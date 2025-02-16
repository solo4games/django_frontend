from prometheus_client import Counter, Summary

request_total = Counter('request_total',
                        'Total number of requests',
                        ['method',
                         'full_path',
                         'ip',
                         'user_agent',
                         'referrer',
                         'http_host',
                         'server_name'])

request_time = Summary('request_processing_seconds',
                       'Time spent processing requests',
                       ['method', 'ip', 'http_host', 'server_name'])


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

        with request_time.labels(method, ip, http_host, server_name).time():
            request_total.labels(method, full_path, ip, user_agent, referrer, http_host, server_name).inc()

            response = self.get_response(request)
            return response
