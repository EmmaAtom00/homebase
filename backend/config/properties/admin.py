from django.contrib import admin

from .models import Property, PropertyPhoto


class PropertyPhotoTabularLine(admin.TabularInline):
    model = PropertyPhoto
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    inlines = [PropertyPhotoTabularLine]
