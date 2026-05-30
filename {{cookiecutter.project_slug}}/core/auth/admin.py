from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin, SimpleHistoryAdmin, BaseUserAdmin):
    list_display = [
        "name_header",
        "email_header",
        "is_active_header",
        "is_staff",
        "is_superuser",
        "date_joined",
    ]
    list_filter = ["is_active", "is_staff", "is_superuser"]
    {%- if cookiecutter.username_type == "email" %}
    search_fields = ["name", "email"]
    {%- else %}
    search_fields = ["name", "email", "username"]
    {%- endif %}
    ordering = ["-date_joined"]
    readonly_fields = ["date_joined", "last_login"]

    @display(description="Name", label=True)
    def name_header(self, obj):
        return obj.name or "-"

    @display(description="Email", label=True)
    def email_header(self, obj):
        return obj.email

    @display(description="Status", label={
        "Active": "success",
        "Inactive": "danger",
    })
    def is_active_header(self, obj):
        return "Active" if obj.is_active else "Inactive"
