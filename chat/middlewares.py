from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user(user_id):
    return User.objects.filter(id=user_id).first()


class JwtAuthTokenMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])

        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode()
            if auth_header.startswith("Bearer"):
                token = auth_header.split(" ")[1]
                access_token = AccessToken(token)
                user = await get_user(access_token['user_id'])
                if user is None:
                    scope['user'] = AnonymousUser()
                else:
                    scope['user'] = user
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
