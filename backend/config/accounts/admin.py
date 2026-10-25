from django.contrib import admin

from .models import User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    ordering = ["email"]
    search_fields = ["email", "firs_name", "last_name"]
    list_filter = ["is_verified", "is_staff", "role"]
