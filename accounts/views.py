from uuid import uuid4
from drf_yasg import openapi
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from .oauth2 import oauth2_sign_in
from .tokens import get_tokens_for_user
from .models import CustomUser, Location
from .tasks import send_to_gmail, send_password_reset_email
from .permissions import IsAdminPermission
from stories.permissions import IsOwnerPermission
from .serializers import (
    EmailVerificationSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
    CustomUserMyProfileSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    CheckUsernameSerializer,
    ChangeEmailSerializer,
    LocationModelSerializer
)



# CustomUserRegisterAPIView view
class CustomUserRegisterAPIView(CreateAPIView):
    permission_classes = (AllowAny,)
    queryset = CustomUser.objects.all()
    serializer_class = UserSignUpSerializer

    @swagger_auto_schema(request_body=UserSignUpSerializer, tags=["auth"])
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

    @swagger_auto_schema(request_body=EmailVerificationSerializer, tags=["auth"])
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
    serializer_class = UserSignInSerializer
    
    @swagger_auto_schema(request_body=UserSignInSerializer, tags=["auth"])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.get(email=serializer.data['email'])
        return Response({'status': True, 'email': serializer.data['email'], 'token': get_tokens_for_user(user)})


# ForgotPassword view
class ForgotPasswordAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgetPasswordSerializer

    @swagger_auto_schema(request_body=ForgetPasswordSerializer, tags=["auth"])
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

    @swagger_auto_schema(request_body=ResetPasswordSerializer, tags=["auth"])
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
        user.set_password(new_password)
        user.save()
        cache.delete(f'password_reset:{reset_link}')
        return Response({"message": "Your password has been successfully updated"})


# CustomUserMyProfileAPIView view
class CustomUserMyProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomUserMyProfileSerializer
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(tags=["accounts"])
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CustomUserMyProfileSerializer, tags=["accounts"])
    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(self.serializer_class(user).data)


# GoogleLoginAPIView view
class GoogleLoginAPIView(APIView):
    permission_classes = (AllowAny,)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='Google OAuth token')
        }
    ), tags=["auth"])
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token required'}, status=400)
        tokens = oauth2_sign_in(token)
        return Response(tokens)


# Checkusername view
class CheckUsernameAPIView(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = CheckUsernameSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'username', openapi.IN_QUERY,
                description="Tekshiriladigan username",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        tags=["accounts"]
    )
    def get(self, request, *args, **kwargs):
        serializer = CheckUsernameSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        username = serializer.validated_data['username']
        exists = CustomUser.objects.filter(username=username.lower()).exists()

        return Response({"available": not exists}, status=200)


# Change Email View
class ChangeEmailAPIView(APIView):
    serializer_class = ChangeEmailSerializer
    permission_classes = (IsAuthenticated, )

    @swagger_auto_schema(request_body=ChangeEmailSerializer, tags=['accounts'])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        email = serializer.data.get("new_email")
        send_to_gmail.apply_async(args=[email], countdown=5)
        cache.set(f'change_email:{email}', request.user, timeout=settings.CACHE_TTL)
        return Response({"message": "A verification code has been sent to your new email address to update your email."}, status=200)


class AcceptChangeEmailAPIView(APIView):
    serializer_class = EmailVerificationSerializer

    @swagger_auto_schema(request_body=EmailVerificationSerializer, tags=['accounts'])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.data.get('code')
        if code and (email := cache.get(f'{settings.CACHE_KEY_PREFIX}:{code}')):
            if user := cache.get(f'change_email:{email}'):
                cache.delete(f'{settings.CACHE_KEY_PREFIX}:{code}')
                cache.delete(f'change_email:{email}')
                user.email = email
                user.save()
                return Response({"message": 'Email successfully updated'})
        return Response({"message": 'Code is expired or invalid'})


# Adminstrators APIs
class AdminUserModelViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserMyProfileSerializer
    permission_classes = (IsAuthenticated, IsAdminPermission)
    http_method_names = ("get", "delete")


# Location modelViewset
class LocationModelViewSet(ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)

    def create(self, request, *args, **kwargs):

        return super().create(request, *args, **kwargs)


# Username and FistName LastName and email search
class ProfileSearchAPIView(APIView):
    serializer_class = CustomUserMyProfileSerializer
    permission_classes = (AllowAny, )

    def get(self, request, key):
        query_users = CustomUser.objects.filter(
            Q(username__icontains=key) |
            Q(first_name__icontains=key) |
            Q(last_name__icontains=key) |
            Q(email__icontains=key)
        )
        serializer = self.serializer_class(query_users, many=True)
        return Response(serializer.data, status=200)
