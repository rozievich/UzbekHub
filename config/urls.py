from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

schema_view = get_schema_view(
   openapi.Info(
      title="UzbekHub API",
      default_version='v1.0',
      description="UzbekHub API documentation",
      terms_of_service="https://github.com/rozievich/UzbekHub",
      contact=openapi.Contact(email="oybekrozievich@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swdoc<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swdoc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('panel/', admin.site.urls),
]
