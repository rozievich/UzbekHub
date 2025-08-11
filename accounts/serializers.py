import re
from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from .models import CustomUser, Location
from chat.consumers import redis_client


# User registration serializer
class UserSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=128)
    password = serializers.CharField(min_length=8, max_length=128)
    confirm_password = serializers.CharField(min_length=8, max_length=255, write_only=True)

    def validate(self, attrs):
        password = attrs.pop('password')
        confirm_password = attrs.pop('confirm_password')
        if password and confirm_password and password == confirm_password:
            attrs['password'] = make_password(password)
            return attrs
        raise ValueError('Password error!')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


# User sign-in serializer
class UserSignInSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=255)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = CustomUser.objects.filter(email=email).first()
        if user and user.check_password(password):
            return attrs
        raise serializers.ValidationError("Incorrect email or password")


# Email verification serializer
class EmailVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5)

    def validate_code(self, value):
        if value.isdigit() and len(value) == 5:
            return value
        raise serializers.ValidationError("The code must consist of 5 digits.")


# Location Model Serializer
class LocationModelSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Location
        fields = "__all__"
        extra_kwargs = {
            "country": {"read_only": True},
            "city": {"read_only": True},
            "county": {"read_only": True},
            "neighbourhood": {"read_only": True},
        }


# CustomUserMyProfileSerializer
class CustomUserMyProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    location = LocationModelSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ("id", "first_name", "last_name", "email", "username", "bio", "location", "profile_picture", "phone", "is_active", "is_staff", "date_joined", "last_login", "password")

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def validate_username(self, value):
        value = value.lower()
        user_qs = CustomUser.objects.filter(username=value)

        if self.instance:
            user_qs = user_qs.exclude(pk=self.instance.pk)

        if user_qs.exists():
            raise serializers.ValidationError(
                "Sorry, this username is taken."
            )

        if not re.match(r'^[A-Za-z0-9._]+$', value):
            raise serializers.ValidationError(
                "Username must contain only letters, numbers, periods, and underscores."
            )

        if value[0] in "._" or value[-1] in "._":
            raise serializers.ValidationError(
                "Username must not start or end with '.' or '_'."
            )

        if '__' in value or '..' in value or '._' in value or '_.' in value:
            raise serializers.ValidationError(
                "Username must not contain consecutive '.' or '_' characters."
            )

        return value

    def to_representation(self, instance):
        represantation = super().to_representation(instance)
        # user_status = redis_client.sismember("online_users", represantation['id'])
        # if user_status:
        #     represantation['last_login'] = "online"
        represantation['groups'] = [{"id": group.id, "name": group.name, "username": group.username} for group in instance.chat_groups.all()]
        return represantation
    

# Forget password serializer
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=128)


# Reset password serializer
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, max_length=128)
    confirm_password = serializers.CharField(min_length=8, max_length=128, write_only=True)

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        if new_password and confirm_password and new_password == confirm_password:
            attrs['new_password'] = new_password
            return attrs
        raise ValueError('Password error!')


# CheckUsernameAPI View
class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=4, max_length=25)

    def validate_username(self, value):
        if not re.match(r'^[A-Za-z0-9._]+$', value):
            raise serializers.ValidationError(
                "Username must contain only letters, numbers, periods, and underscores."
            )

        if value[0] in "._" or value[-1] in "._":
            raise serializers.ValidationError(
                "Username must not start or end with '.' or '_'."
            )

        if '__' in value or '..' in value or '._' in value or '_.' in value:
            raise serializers.ValidationError(
                "Username must not contain consecutive '.' or '_' characters."
            )

        return value


# ChangeEmailSerializer
class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('new_email')
        password = attrs.get('password')
        user = self.context["request"].user

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered in the system.")
        
        if not user.check_password(password):
            raise serializers.ValidationError({"current_password": "The password is incorrect."})
        return attrs
