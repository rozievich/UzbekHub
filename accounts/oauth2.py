from django.conf import settings
from django.contrib.auth.hashers import make_password
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

from .models import CustomUser
from .tokens import get_tokens_for_user


def oauth2_sign_in(token):
    try:
        response = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        email = response.get('email')
        if not email:
            raise AuthenticationFailed('Google account has no email', status.HTTP_400_BAD_REQUEST)
        
        first_name = response.get('given_name', '')
        last_name = response.get('family_name', '')
        picture = response.get('picture', None)

        password = make_password(email + settings.SECRET_KEY)
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'password': password,
                'is_active': True,
                'profile_picture': picture,
            }
        )
        if not created:
            updated = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if not user.is_active:
                user.is_active = True
                updated = True
            if updated:
                user.save()
        return get_tokens_for_user(user)
    except ValueError:
        raise AuthenticationFailed('Google token is invalid or expired.', status.HTTP_403_FORBIDDEN)
