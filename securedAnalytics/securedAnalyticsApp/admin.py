from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users, Person, Address


@admin.register(Users)
class UsersAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "middle_name", "last_name", "name_suffix", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "middle_name", "last_name", "name_suffix")
    list_filter = ("is_active", "is_staff", "date_joined")
    ordering = ("-date_joined",)

    # Extend the default UserAdmin fieldsets to include custom fields
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("middle_name", "name_suffix")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("middle_name", "name_suffix")}),
    )


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "ethnicity", "city", "state", "created_at")
    list_select_related = ("user",)
    search_fields = ("user__username", "phone_number", "city")
    list_filter = ("ethnicity", "city", "state", "created_at")
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("person", "street_address", "city", "state", "address_type", "is_primary", "created_at")
    list_select_related = ("person",)
    search_fields = ("person__user__username", "street_address", "city")
    list_filter = ("address_type", "is_primary", "state", "created_at")
    ordering = ("-created_at",)
