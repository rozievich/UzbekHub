from uuid import uuid4
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, UpdateAPIView, DestroyAPIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from .oauth2 import oauth2_sign_in
from .tokens import get_tokens_for_user
from accounts.utils.get_location import get_my_location
from .models import CustomUser, Location, UserBlock, Status
from .tasks import delete_account_email, send_to_gmail, send_password_reset_email
from stories.permissions import IsOwnerPermission
from .permissions import IsAdminPermission
from .serializers import (
    EmailVerificationSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
    CustomUserMyProfileSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    CheckUsernameSerializer,
    ChangeEmailSerializer,
    LocationModelSerializer,
    UserBlockSerializer,
    UserStatusModelSerializer,
    DeleteAccountSerializer
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
        cache_key = f'user:{user.email}'
        if cache.get(cache_key):
            ttl = cache.ttl(cache_key)
            if ttl is None:
                ttl = 0
            return Response({
                "message": "Sign up process already started",
                "wait_seconds": ttl
            }, status=429)
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
        cache_key = f'password_reset:{reset_link}'
        if cache.get(cache_key):
            ttl = cache.ttl(cache_key)
            if ttl is None:
                ttl = 0
            return Response({
                "message": "Reset password process already started",
                "wait_seconds": ttl
            }, status=429)
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


# Delete account
class UserDeleteRequestAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeleteAccountSerializer

    @swagger_auto_schema(
        request_body=DeleteAccountSerializer,
        tags=["accounts"]
    )
    def post(self, request, *args, **kwargs):
        serializer_class = self.serializer_class(data=request.data, context={"request": request})
        serializer_class.is_valid(raise_exception=True)

        user = request.user
        cache_key = f'delete_user:{user.email}'
        if cache.get(cache_key):
            ttl = cache.ttl(cache_key)
            if ttl is None:
                ttl = 0
            return Response({
                "message": "Delete process already started",
                "wait_seconds": ttl
            }, status=429)
        delete_account_email.apply_async(args=[user.email], countdown=5)
        cache.set(f'delete_user:{user.email}', user, timeout=settings.CACHE_TTL)
        return Response({"message": "Verification code sent to email"}, status=200)


class AcceptDeleteAccountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        request_body=EmailVerificationSerializer,
        tags=["accounts"]
    )
    def post(self, request, *args, **kwargs):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.data.get("code")
        user = request.user

        if code and (email := cache.get(f'delete_user_cache:{code}')):
            if user := cache.get(f'delete_user:{email}'):
                cache.delete(f'delete_user_cache:{code}')
                cache.delete(f'user:{email}')
                user.delete()
                return Response({"message": "Account successfully deleted"}, status=204)

        return Response({"error": "Invalid or expired code"}, status=400)


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


# Locations Views
class LocationAPIView(CreateAPIView, UpdateAPIView, DestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)
    http_method_names = ("post", "delete", "put")

    def create(self, request, *args, **kwargs):
        user_location = self.queryset.filter(owner=request.user).first()
        if user_location:
            return Response({"error": "Location already exists. You can update it instead."}, status=400)
        
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data.get('lat')
        long = serializer.validated_data.get('long')
        full_address = get_my_location(lat=str(lat), long=str(long))
        
        if full_address:
            serializer.save(
                country=full_address.get('country'),
                city=full_address.get('city'),
                county=full_address.get('county'),
                neighbourhood=full_address.get('neighbourhood')
            )
        else:
            serializer.save()
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        user_location = self.queryset.filter(owner=request.user).first()
        if user_location:
            serializer = self.serializer_class(user_location, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            lat = serializer.validated_data.get('lat')
            long = serializer.validated_data.get('long')
            full_address = get_my_location(lat=str(lat), long=str(long))
            if full_address:
                serializer.save(
                    country=full_address.get('country'),
                    city=full_address.get('city'),
                    county=full_address.get('county'),
                    neighbourhood=full_address.get('neighbourhood')
                )
            else:
                serializer.save()
            return Response(serializer.data, status=200)
        return Response({"error": "Location not found"}, status=404)

    def destroy(self, request, *args, **kwargs):
        Location.objects.filter(owner=request.user).delete()
        return Response(status=204)


# Username and FistName LastName and email search
class ProfileSearchAPIView(APIView):
    serializer_class = CustomUserMyProfileSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, key):
        blocked_me = UserBlock.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)
        query_users = CustomUser.objects.filter(username__icontains=key).exclude(id__in=blocked_me)
        serializer = self.serializer_class(query_users, many=True)
        return Response(serializer.data, status=200)


class ProfileDetailAPIView(APIView):
    serializer_class = CustomUserMyProfileSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, pk):
        blocked_me = UserBlock.objects.filter(blocked_user=request.user).values_list('user_id', flat=True)
        user = CustomUser.objects.filter(id=pk).exclude(id__in=blocked_me).first()
        if not user:
            return Response({"error": "User not found"}, status=404)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=200)


# Block and Unblock Users
class BlockedUsersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserBlockSerializer

    def get(self, request, *args, **kwargs):
        blocked_users = UserBlock.objects.filter(user=request.user)
        serializer = self.serializer_class(blocked_users, many=True, context={"request": request})
        return Response(serializer.data, status=200)

    @swagger_auto_schema(tags=["accounts"])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)


# Retrieve + Delete
class BlockedUserDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserBlockSerializer

    @swagger_auto_schema(tags=["accounts"])
    def get(self, request, pk):
        blocked_user = UserBlock.objects.filter(user=request.user, blocked_user=pk).first()
        if not blocked_user:
            return Response({"error": "Not found"}, status=404)
        serializer = self.serializer_class(blocked_user, context={"request": request})
        return Response(serializer.data, status=200)

    @swagger_auto_schema(tags=["accounts"])
    def delete(self, request, pk):
        blocked_user = UserBlock.objects.filter(user=request.user, blocked_user=pk).first()
        if not blocked_user:
            return Response({"error": "Not found"}, status=404)
        blocked_user.delete()
        return Response(status=204)


# User Status APIView
class UserStatusAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserStatusModelSerializer

    def get(self, request, *args, **kwargs):
        try:
            status = request.user.status
            serializer = self.serializer_class(status)
            return Response(serializer.data, status=200)
        except Status.DoesNotExist:
            return Response({"detail": "No status found"}, status=404)

    @swagger_auto_schema(request_body=UserStatusModelSerializer, tags=["accounts"])
    def post(self, request, *args, **kwargs):
        if hasattr(request.user, 'status'):
            return Response({"error": "Status already exists. You can update it instead."}, status=400)
        
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)

    @swagger_auto_schema(request_body=UserStatusModelSerializer, tags=["accounts"])
    def put(self, request, *args, **kwargs):
        try:
            status = request.user.status
            serializer = self.serializer_class(status, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=200)
        except Status.DoesNotExist:
            return Response({"error": "No status found to update"}, status=404)

    def delete(self, request, *args, **kwargs):
        try:
            status = request.user.status
            status.delete()
            return Response(status=204)
        except Status.DoesNotExist:
            return Response({"error": "No status found to delete"}, status=404)


# Adminstrators APIs
class AdminUserModelViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserMyProfileSerializer
    permission_classes = (IsAuthenticated, IsAdminPermission)
    http_method_names = ("get", "delete")
