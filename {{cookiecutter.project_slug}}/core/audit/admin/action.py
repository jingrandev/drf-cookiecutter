from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import Action


@admin.register(Action)
class ActionAdmin(ModelAdmin):
    list_display = ["type", "user", "scope", "description", "created_at", "undone_at"]
    list_filter = ["type", "created_at"]
    search_fields = ["type", "description", "params"]
    readonly_fields = ["params_pretty", "created_at", "updated_at"]
    raw_id_fields = ["user"]

    def params_pretty(self, obj):
        if obj.params:
            import json

            return json.dumps(obj.params, indent=2, ensure_ascii=False)
        return "-"

    params_pretty.short_description = "Params (JSON)"
