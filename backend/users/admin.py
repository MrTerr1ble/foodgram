from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar'
    )
    list_display_links = (
        'username',
        'email',
    )
    search_fields = (
        'first_name',
        'last_name',
        'email',
    )
    list_filter = (
        'is_superuser',
        'is_active',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user__email', 'user__username')
