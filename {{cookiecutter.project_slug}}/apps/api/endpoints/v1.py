from django.urls import include, path

app_name = "v1"


endpoints = [
    path("", include("apps.api.urls")),
    path("auth/", include("core.auth.urls")),
]

urlpatterns = [
    path("v1/", include(endpoints)),
]
