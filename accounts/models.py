from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError

from .validators import validate_lat, validate_long, validate_phone_number, validate_username


# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


# Custom User Model
class CustomUser(AbstractUser):
    username = models.CharField(max_length=25, blank=True, null=True, validators=[validate_username])
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True, validators=[validate_phone_number])
    is_private = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    last_online = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def clean(self):
        if self.username:
            if CustomUser.objects.filter(username=self.username).exclude(pk=self.pk).exists():
                raise ValidationError({"username": "This username already exists."})
        return super().clean()

    def __str__(self):
        return self.email


class Location(models.Model):
    owner = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="location")
    lat = models.CharField(max_length=50, validators=[validate_lat])
    long = models.CharField(max_length=50, validators=[validate_long])
    country = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    county = models.CharField(max_length=128, blank=True, null=True)
    neighbourhood = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        parts = [self.country, self.city, self.county, self.neighbourhood]
        return ", ".join(filter(None, parts))


class UserBlock(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blocked_users")
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="blocked_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f"{self.user.email} blocked {self.blocked_user.email}"


class Status(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="status")
    content = models.CharField(max_length=55)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Status by {self.user.email} at {self.created_at}"


class Contact(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="contact_lists")
    contact = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="in_contact_list")
    nikname = models.CharField(max_length=80, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nikname

    