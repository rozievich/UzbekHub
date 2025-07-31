from hashlib import new
from uuid import uuid4
from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .tokens import get_tokens_for_user
from .tasks import send_to_gmail, send_password_reset_email
from .models import CustomUser
from .serializers import (
    CustomTokenSerializer,
    EmailVerificationSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
    CustomUserMyProfileSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer
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


# ForgotPassword view
class ForgotPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data.get('email')
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User with this email does not exist"}, status=404)

        reset_link = uuid4().hex
        send_password_reset_email.apply_async(args=[email, reset_link], countdown=5)

        cache.set(f'password_reset:{reset_link}', user.email, timeout=settings.CACHE_TTL)
        return Response({"message": "Password reset link has been sent to your email"})


# NewPassword view
class NewPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, reset_link, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = cache.get(f'password_reset:{reset_link}')
        if not email:
            return Response({"error": "Invalid or expired token"}, status=400)

        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User with this email does not exist"}, status=404)
        
        new_password = serializer.data.get('new_password')
        user.password = make_password(new_password)
        user.save()
        cache.delete(f'password_reset:{reset_link}')
        return Response({"message": "Your password has been successfully updated"})


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
