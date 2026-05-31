from django.conf import settings
from django.db import models
from django.db.models import Index


class Action(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="actions",
    )
    type = models.TextField(db_index=True)
    params = models.JSONField(default=dict)
    scope = models.TextField(db_index=True, default="root")
    description = models.TextField(blank=True, default="")
    session = models.TextField(null=True, blank=True, db_index=True)
    undone_at = models.DateTimeField(null=True, blank=True, db_index=True)
    error = models.TextField(null=True, blank=True)
    action_group = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["-created_at", "-id"]),
            Index(fields=["-undone_at", "-id"]),
        ]

    def __str__(self):
        return f"Action({self.type}, user={self.user_id}, scope={self.scope})"
