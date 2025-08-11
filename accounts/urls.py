from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.views import (
    CustomUserRegisterAPIView,
    EmailVerifyCreateAPIView,
    CustomUserSignInAPIView,
    CustomUserMyProfileAPIView,
    ForgotPasswordAPIView,
    NewPasswordAPIView,
    GoogleLoginAPIView,
    CheckUsernameAPIView,
    ChangeEmailAPIView,
    AcceptChangeEmailAPIView,
    AdminUserModelViewSet,
    ProfileSearchAPIView,
    LocationModelViewSet
)

router = DefaultRouter()
router.register(r'admin/user', AdminUserModelViewSet, basename="admins")
router.register('location', LocationModelViewSet, basename="locations")


urlpatterns = [
    path('auth/signup/', CustomUserRegisterAPIView.as_view(), name='user_signup'),
    path('auth/signin/', CustomUserSignInAPIView.as_view(), name='user_signin'),
    path('auth/oauth2/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('auth/email-verify/', EmailVerifyCreateAPIView.as_view(), name='email_verify'),
    path('auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path('auth/reset-password/<str:reset_link>/', NewPasswordAPIView.as_view(), name='reset_password'),
    
    path('account/profile/', CustomUserMyProfileAPIView.as_view(), name='user_my_profile'),
    path('account/check/username/', CheckUsernameAPIView.as_view(), name="check_username"),
    path('account/change-email/', ChangeEmailAPIView.as_view(), name="change_email"),
    path('account/change-email/confirm/', AcceptChangeEmailAPIView.as_view(), name="change_email_confirm"),
    path('account/search/<str:key>/', ProfileSearchAPIView.as_view(), name="profile_search"),
    path('', include(router.urls))
]
