from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .tokens import get_tokens_for_user
from .tasks import send_to_gmail
from .models import CustomUser
from .serializers import (
    CustomTokenSerializer,
    EmailVerificationSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
    CustomUserMyProfileSerializer
)



# CustomToken view
class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


# CustomUserRegisterAPIView view
class CustomUserRegisterAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    queryset = CustomUser.objects.all()
    serializer_class = UserSignUpSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        user = CustomUser(**data)
        send_to_gmail.apply_async(args=[user.email], countdown=5)
        cache.set(f'user:{user.email}', user, timeout=settings.CACHE_TTL)
        return Response({"status": True, 'user': user.email}, status=201)


# EmailVerify view
class EmailVerifyCreateAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailVerificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.data.get('code')
        if code and (email := cache.get(f'{settings.CACHE_KEY_PREFIX}:{code}')):
            if user := cache.get(f'user:{email}'):
                cache.delete(f'{settings.CACHE_KEY_PREFIX}:{code}')
                cache.delete(f'user:{email}')
                user.save()
                return Response({"message": 'User is successfully activated'})
        return Response({"message": 'Code is expired or invalid'})


# CustomUserSignInAPIView view
class CustomUserSignInAPIView(APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request, *args, **kwargs):
        serializer = UserSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.get(email=serializer.data['email'])
        return Response({'status': True, 'email': serializer.data['email'], 'token': get_tokens_for_user(user)})


# CustomUserMyProfileAPIView view
class CustomUserMyProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomUserMyProfileSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(self.serializer_class(user).data)
