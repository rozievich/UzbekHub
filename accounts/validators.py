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
