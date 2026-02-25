from django.contrib import admin
from .models import Users, Person, Address


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_active", "created_at")
    search_fields = ("username", "email")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "ethnicity", "city", "state", "created_at")
    search_fields = ("user__username", "phone_number", "city")
    list_filter = ("ethnicity", "city", "state", "created_at")
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("person", "street_address", "city", "state", "address_type", "is_primary", "created_at")
    search_fields = ("person__user__username", "street_address", "city")
    list_filter = ("address_type", "is_primary", "state", "created_at")
    ordering = ("-created_at",)
