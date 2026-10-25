from django.contrib import admin
from .models import User

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    ordering = ['email']
    search_fields = ['email']
    list_filter = ['is_verified']

