from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_phone_number(value):
    phone_validator = RegexValidator(
        regex=r'^\+998[123456789]\d{8}$',
        message='Please enter your phone number correctly, for example: +998901234567',
        code='invalid_phone_number'
    )
    try:
        phone_validator(value)
    except ValidationError as e:
        raise ValidationError(e.messages)


def validate_username(value):
    username_validator = RegexValidator(
        regex=r'^[A-Za-z0-9._]+$',
        message="Username must contain only letters, numbers, periods, and underscores.",
        code="invalid_username"
    )
    try:
        username_validator(value)
    except ValidationError as e:
        raise ValidationError(e.message)

def validate_lat(value):
    try:
        val = float(value)
    except ValueError:
        raise ValidationError("Latitude son bo‘lishi kerak.")
    if val < -90 or val > 90:
        raise ValidationError("Latitude -90 va 90 oralig‘ida bo‘lishi kerak.")

def validate_long(value):
    try:
        val = float(value)
    except ValueError:
        raise ValidationError("Longitude son bo‘lishi kerak.")
    if val < -180 or val > 180:
        raise ValidationError("Longitude -180 va 180 oralig‘ida bo‘lishi kerak.")
