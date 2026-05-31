from django.urls import include
from django.urls import path

from core.restframework.routers import get_router

from .endpoints import ActionViewSet

router = get_router()
router.register("actions", ActionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
