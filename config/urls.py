from django.contrib import admin
from django.urls import include, path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


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
    path('api/accounts/', include('accounts.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/stories/', include('stories.urls')),
    path('panel/', admin.site.urls),
]
