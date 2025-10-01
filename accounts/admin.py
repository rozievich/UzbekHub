from django.contrib import admin

from .models import CustomUser, PremiumUsername

admin.site.register(CustomUser)
admin.site.register(PremiumUsername)
