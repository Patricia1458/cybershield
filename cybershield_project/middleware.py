from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Adds a Content-Security-Policy header, since Django has no built-in setting for it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        policy = getattr(settings, 'CSP_POLICY', None)
        if policy:
            response['Content-Security-Policy'] = policy
        return response
