from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    CustomTokenView,
    CustomUserRegisterAPIView,
    EmailVerifyCreateAPIView,
    CustomUserSignInAPIView,
    CustomUserMyProfileAPIView,
    ForgotPasswordAPIView,
    NewPasswordAPIView,
    GoogleLoginAPIView,
    CheckUsernameAPIView
)


urlpatterns = [
    path('token/', CustomTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', CustomUserRegisterAPIView.as_view(), name='user_signup'),
    path('email-verify/', EmailVerifyCreateAPIView.as_view(), name='email_verify'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path('reset-password/<str:reset_link>/', NewPasswordAPIView.as_view(), name='reset_password'),
    path('signin/', CustomUserSignInAPIView.as_view(), name='user_signin'),
    path('oauth2/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('profile/', CustomUserMyProfileAPIView.as_view(), name='user_my_profile'),
    path('check/username/', CheckUsernameAPIView.as_view(), name="check_username")
]
