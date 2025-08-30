from random import randint

from celery import shared_task
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from config import settings
from config.settings import EMAIL_HOST_USER


@shared_task
def send_to_gmail(email):
    otp_code = str(randint(10000, 99999))
    cache.set(f'{settings.CACHE_KEY_PREFIX}:{otp_code}', email, timeout=settings.CACHE_TTL)
    subject = 'Your UzbekHub verification code'

    message = render_to_string('email_template.html', {'code': otp_code})

    recipient_list = [email]

    email = EmailMessage(subject, message, EMAIL_HOST_USER, recipient_list)
    email.content_subtype = 'html'
    result = email.send()
    return result


@shared_task
def send_password_reset_email(email, reset_link):
    user = cache.get(f'password_reset:{reset_link}')
    if not user:
        return False

    subject = 'Your UzbekHub password recovery request'
    message = render_to_string('forget_password.html', {'reset_link': f"{settings.FRONTEND_URL}/auth/reset-link/{reset_link}/"})

    recipient_list = [email]
    
    email = EmailMessage(subject, message, EMAIL_HOST_USER, recipient_list)
    email.content_subtype = 'html'
    result = email.send()
    return result


@shared_task
def delete_account_email(email):
    otp_code = str(randint(10000, 99999))
    cache.set(f'delete_user_cache:{otp_code}', email, timeout=settings.CACHE_TTL)
    subject = 'Your UzbekHub profile deletion request'

    message = render_to_string('delete_account.html', {'code': otp_code})

    recipient_list = [email]

    email = EmailMessage(subject, message, EMAIL_HOST_USER, recipient_list)
    email.content_subtype = 'html'
    result = email.send()
    return result
