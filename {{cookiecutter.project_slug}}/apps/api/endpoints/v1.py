from django.urls import include, path

app_name = "v1"


endpoints = [
    path("", include("apps.api.urls")),
    path("auth/", include("core.auth.urls")),
    {%- if cookiecutter.use_action_audit == "yes" %}
    path("audit/", include("core.audit.urls")),
    {%- endif %}
]

urlpatterns = [
    path("v1/", include(endpoints)),
]
