from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'

    def authenticate_header(self, request):
        return 'Bearer'

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            return None


def custom_exception_handler(exc, context):
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            {"message": "Login failed"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return None 