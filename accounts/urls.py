from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from accounts.views import (
    CustomTokenView,
    CustomUserRegisterAPIView,
    EmailVerifyCreateAPIView,
    CustomUserSignInAPIView,
    CustomUserMyProfileAPIView
)


urlpatterns = [
    path('token/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('signup/', CustomUserRegisterAPIView.as_view(), name='user_signup'),
    path('email-verify/', EmailVerifyCreateAPIView.as_view(), name='email_verify'),
    path('signin/', CustomUserSignInAPIView.as_view(), name='user_signin'),
    path('profile/', CustomUserMyProfileAPIView.as_view(), name='user_my_profile'),
]
